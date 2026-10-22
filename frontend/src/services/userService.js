import API from "./api";

export const getProfile = (userId) => {
  return API.get(`/users/profile?user_id=${userId}`);
};

export const updateProfile = (payload) => {
  return API.put("/users/profile", payload);
};

export const checkUsernameAvailability = (username) => {
  return API.get(`/users/users/check-username?username=${encodeURIComponent(username)}`);
};

export const uploadProfileImage = (userId, file) => {
  const form = new FormData();
  form.append("file", file);

  return API.post(`/users/users/${userId}/profile/image`, form, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });
};