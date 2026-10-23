import API from "./api";

export const getWallet = (userId) => {
  return API.get(`/users/wallet?user_id=${userId}`);
};

export const getWalletHistory = (userId, page = 1) => {
  return API.get(`/users/wallet/history?user_id=${userId}&page=${page}`);
};

export const getWalletBalance = (userId) => {
  return API.get(`/users/wallet/balance?user_id=${userId}`);
};