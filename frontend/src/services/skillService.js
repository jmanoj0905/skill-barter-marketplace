import API from "./api";

export const getSkills = (userId) => {
  return API.get(`/api/skills/user/${userId}`);
};

export const createSkill = (payload) => {
  return API.post("/api/skills", payload);
};

export const updateSkill = (skillId, payload) => {
  return API.put(`/api/skills/${skillId}`, payload);
};

export const deleteSkill = (skillId, userId) => {
  return API.delete(`/api/skills/${skillId}?user_id=${userId}`);
};

export const suggestSkills = (query) => {
  return API.get(`/api/skills/suggestions?query=${encodeURIComponent(query)}`);
};
