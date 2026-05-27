// 用户信息管理工具

export const getUserInfo = () => {
  try {
    const userInfo = localStorage.getItem('userInfo');
    if (userInfo) {
      return JSON.parse(userInfo);
    }
    return null;
  } catch (e) {
    console.error("获取用户信息失败:", e);
    return null;
  }
};

export const getUserId = () => {
  const user = getUserInfo();
  if (user && user.id) {
    const userId = parseInt(user.id, 10);
    return isNaN(userId) ? null : userId;
  }
  return null;
};

export const isLoggedIn = () => {
  return localStorage.getItem('isLoggedIn') === 'true';
};

export const logout = () => {
  localStorage.removeItem('isLoggedIn');
  localStorage.removeItem('username');
  localStorage.removeItem('userRole');
  localStorage.removeItem('userInfo');
};
