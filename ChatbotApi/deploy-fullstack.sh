#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p logs
    
    # 检查前端代码目录是否存在
    if [ ! -d "Chatbot" ]; then
        log_warning "Chatbot目录不存在，正在从GitHub拉取前端代码..."
        if git clone -b sso git@github.com:ZhuoranZhao/Chatbot.git Chatbot; then
            log_success "前端代码拉取成功"
        else
            log_error "从GitHub拉取前端代码失败。请检查git是否安装、SSH密钥是否配置正确或网络连接。"
            exit 1
        fi
    else
        log_warning "发现Chatbot目录，更新前端代码"
        if sudo rm -rf Chatbot; then
            log_success "Chatbot目录删除成功"
        else
            log_error "Chatbot目录删除失败"
        fi
        if git clone -b sso git@github.com:ZhuoranZhao/Chatbot.git Chatbot; then
            log_success "前端代码拉取成功"
        else
            log_error "从GitHub拉取前端代码失败。请检查git是否安装、SSH密钥是否配置正确或网络连接。"
            exit 1
        fi
    fi
    
    log_success "目录检查完成"
}

# 检查环境变量
check_env() {
    log_info "检查环境变量..."
    
    if [ -z "$DASHSCOPE_API_KEY" ]; then
        log_warning "DASHSCOPE_API_KEY未设置，查找 .env"
    fi
    # 检查.env文件
    if [ -f ".env" ]; then
        log_info "发现.env文件，将使用其中的配置"
        source .env
    else
        log_error "环境变量 DASHSCOPE_API_KEY 未正确设置，请检查环境变量"
    fi
}

# 构建和启动服务
deploy() {
    log_info "开始部署服务..."
    
    # 停止并移除现有容器
    log_info "停止现有服务..."
    if command -v docker-compose &> /dev/null; then
        docker-compose down --remove-orphans
    else
        docker compose down --remove-orphans
    fi
    
    # 清理未使用的镜像（可选）
    if [ "$1" = "--clean" ]; then
        log_info "清理未使用的Docker镜像..."
        docker system prune -f
    fi
    
    # 构建镜像
    log_info "构建Docker镜像..."
    if command -v docker-compose &> /dev/null; then
        docker-compose build --no-cache
    else
        docker compose build --no-cache
    fi
    
    if [ $? -ne 0 ]; then
        log_error "镜像构建失败"
        exit 1
    fi
    
    # 启动服务
    log_info "启动服务..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi
    
    if [ $? -ne 0 ]; then
        log_error "服务启动失败"
        exit 1
    fi
    
    log_success "服务启动成功"
}

# 检查服务状态
check_services() {
    log_info "检查服务状态..."
    
    sleep 10  # 等待服务启动
    
    # 检查各个服务的健康状态
    services=("chatbot_redis" "chatbot_api" "chatbot_frontend")

    for service in "${services[@]}"; do
        if docker ps | grep -q "$service"; then
            health=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null)
            if [ "$health" = "healthy" ] || [ "$health" = "" ]; then
                log_success "$service 运行正常"
            else    
                log_warning "$service 健康检查未通过: $health"
            fi
        else
            log_error "$service 未运行"
        fi
    done
    
    # 检查端口
    log_info "检查端口占用..."
    if ss -tuln | grep -q ":80 " 2>/dev/null || netstat -tuln | grep -q ":80 " 2>/dev/null; then
        log_success "Nginx (端口80) 正在运行"
    else
        log_error "Nginx (端口80) 未启动"
    fi
}

# 显示日志
show_logs() {
    log_info "显示服务日志..."
    if command -v docker-compose &> /dev/null; then
        docker-compose logs --tail=50 -f
    else
        docker compose logs --tail=50 -f
    fi
}

# 显示帮助信息
show_help() {
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --clean     部署前清理未使用的Docker镜像"
    echo "  --logs      部署后显示服务日志"
    echo "  --status    只检查服务状态"
    echo "  --help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                # 标准部署"
    echo "  $0 --clean        # 清理后部署"
    echo "  $0 --logs         # 部署并显示日志"
    echo "  $0 --status       # 检查服务状态"
}

# 主函数
main() {
    case "$1" in
        --help)
            show_help
            exit 0
            ;;
        --status)
            check_services
            exit 0
            ;;
        *)
            log_info "🚀 开始Chatbot全栈应用部署..."
            
            create_directories
            check_env
            deploy "$1"
            check_services
            
            log_success "🎉 部署完成！"
            log_info "📱 访问地址："
            log_info "   - 前端应用: http://localhost"
            log_info "   - API接口: http://localhost/api"
            log_info "   - API文档: http://localhost/api/docs"
            log_info "   - 健康检查: http://localhost/health"
            log_info ""
            log_info "🔧 管理命令："
            log_info "   - 查看日志: docker-compose logs -f"
            log_info "   - 停止服务: docker-compose down"
            log_info "   - 重启服务: docker-compose restart"
            
            if [ "$1" = "--logs" ]; then
                show_logs
            fi
            ;;
    esac
}

# 执行主函数
main "$@"
