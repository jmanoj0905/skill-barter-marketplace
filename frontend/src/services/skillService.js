import API from "./api";

export const getSkills = (userId) => {
  return API.get(`/users/skills?user_id=${userId}`);
};

export const createSkill = (payload) => {
  return API.post("/users/skills", payload);
};

export const updateSkill = (skillId, payload) => {
  return API.put(`/users/skills/${skillId}`, payload);
};

export const deleteSkill = (skillId, userId) => {
  return API.delete(`/users/skills/${skillId}?user_id=${userId}`);
};

export const suggestSkills = (query) => {
  return API.get(`/users/skills/suggestions?query=${encodeURIComponent(query)}`);
};
