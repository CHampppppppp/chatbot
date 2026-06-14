const { $axios } = useNuxtApp();
export async function getUserInfo(code, fromBusiness) {
  try {
    const response = await $axios.get(
      `/users/user_info?code=${code}&fromBusiness=${fromBusiness}`
    );
    return response;
  } catch (error) {
    console.error("Get User Info Error:", error);
    throw error;
  }
}

// 处理 SSO 重定向后的查询参数
export function handleSSOCallback() {
  if (typeof window === "undefined") return null;

  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get("code");
  const state = urlParams.get("state");
  const fromBusiness = urlParams.get("fromBusiness");

  if (code) {
    return { code, state, fromBusiness };
  }

  return null;
}

// 自动处理 SSO 回调并获取用户信息
export async function autoHandleSSOCallback() {
  try {
    const ssoParams = handleSSOCallback();
    if (!ssoParams) {
      return null; // 没有 SSO 参数，不是从 SSO 重定向来的
    }

    const { code, state, fromBusiness } = ssoParams;

    // 获取用户信息
    const userInfo = await getUserInfo(code, fromBusiness);

    return userInfo;
  } catch (error) {
    console.error("Auto handle SSO callback error:", error);
    throw error;
  }
}
