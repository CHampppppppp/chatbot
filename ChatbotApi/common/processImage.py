#  base 64 编码格式
import base64
import os
import uuid
from pdf2image import convert_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError,
)
from common.BaseResponse import BaseResponse


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def generated_unique_filename(image):
    # 生成唯一文件名，保存到 uploads 目录
    # 使用应用根目录而不是当前工作目录
    upload_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads"
    )
    os.makedirs(upload_dir, exist_ok=True)

    # 初始化image_url变量
    image_url = None

    # 获取文件扩展名，确保正确性
    filename = getattr(image, "filename", "")

    if not filename:
        # 尝试访问file属性
        file_obj = getattr(image, "file", None)
        if file_obj:
            # 尝试获取file对象的name属性
            filename = getattr(file_obj, "name", "")

            # 尝试其他可能的属性
            if not filename:
                filename = getattr(file_obj, "_name", "")

    # 如果仍然没有获取到文件名，使用默认值
    filename = filename or "uploaded_file"
    file_ext = os.path.splitext(filename)[-1].lower()

    # 检查是否为PDF文件
    if file_ext == ".pdf":
        try:
            # 保存PDF文件到临时位置
            temp_pdf_path = os.path.join(upload_dir, f"{uuid.uuid4().hex}.pdf")
            with open(temp_pdf_path, "wb") as f:
                while chunk := image.file.read(8192):
                    f.write(chunk)

            # 将PDF转换为图像
            try:
                images = convert_from_path(temp_pdf_path)
            except PDFInfoNotInstalledError:
                print(f"[DEBUG] 转换失败: poppler-utils未安装")
                return BaseResponse(
                    "操作失败", code=500, err="PDF转换失败: poppler-utils未安装"
                )
            except PDFPageCountError:
                print(f"[DEBUG] 转换失败: 未找到页面")
                return BaseResponse("操作失败", code=500, err="PDF转换失败: 未找到页面")
            except PDFSyntaxError:
                print(f"[DEBUG] 转换失败: 语法错误")
                return BaseResponse("操作失败", code=500, err="PDF转换失败: 语法错误")
            if not images:
                return BaseResponse("操作失败", code=500, err="PDF转换失败: 未找到页面")
            for i in images:
                print(f"[DEBUG]转换后的图像: {i}")

            # 取第一页作为代表图像
            file_name = f"{uuid.uuid4().hex}.png"
            file_path = os.path.join(upload_dir, file_name)
            images[0].save(file_path, "PNG")

            # 删除临时PDF文件
            os.remove(temp_pdf_path)

            # 构造文件URL，使用绝对路径
            image_url = os.path.abspath(file_path)
            return image_url
        except Exception as e:
            return BaseResponse("操作失败", code=500, err=f"PDF处理失败: {str(e)}")
    else:
        # 处理图片文件
        # 如果没有扩展名或不是图片扩展名，默认为.png
        if not file_ext or file_ext not in [
            ".jpg",
            ".jpeg",
            ".png",
            ".tiff",
            ".bmp",
            ".webp",
        ]:
            file_ext = ".png"  # 默认的图片扩展名

        file_name = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(upload_dir, file_name)

        # 保存图片到本地，使用流式读取以处理大文件
        try:
            with open(file_path, "wb") as f:
                # 分块读取和写入
                while chunk := image.file.read(8192):
                    f.write(chunk)
        except Exception as e:
            return BaseResponse("操作失败", code=500, err=f"图片保存失败: {str(e)}")

        # 构造文件URL，使用绝对路径
        image_url = os.path.abspath(file_path)

        return image_url
