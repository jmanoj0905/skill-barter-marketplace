import API from "./api";

const withFingerprintHeader = (fingerprint) => {
  if (!fingerprint) return {};
  return {
    headers: {
      "X-Device-Fingerprint": fingerprint
    }
  };
};

export const registerUser = (data, fingerprint) => {
  return API.post("/auth/register", data, withFingerprintHeader(fingerprint));
};

export const loginUser = (data, fingerprint) => {
  return API.post("/auth/login", data, withFingerprintHeader(fingerprint));
};

export const verifyOTP = (data) => {
  return API.post("/auth/verify-email-otp", data);
};

export const generateEmailOTP = (email) => {
  return API.post("/auth/generate-email-otp", { email });
};

export const resendEmailOTP = (email) => {
  return API.post("/auth/resend-email-otp", { email });
};

export const forgotPassword = (email) => {
  return API.post("/auth/forgot-password", { email });
};

export const resetPassword = (token, newPassword) => {
  return API.post("/auth/reset-password", {
    token,
    new_password: newPassword
  });
};

export const generatePhoneOTP = (phone) => {
  return API.post("/auth/generate-phone-otp", { phone });
};

export const verifyPhoneOTP = (phone, otp) => {
  return API.post("/auth/verify-phone-otp", { phone, otp });
};

export const logoutUser = () => {
  return API.post("/auth/logout");
};