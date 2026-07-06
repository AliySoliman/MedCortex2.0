import api from "./api";
import type {
  AuthResponse,
  GoogleAuthPayload,
  LoginPayload,
  SignupPayload,
} from "@/types/user";

export async function login(payload: LoginPayload): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>("/auth/login", payload);
  return response.data;
}

export async function signup(payload: SignupPayload): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>("/auth/signup", payload);
  return response.data;
}

export async function loginWithGoogle(payload: GoogleAuthPayload): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>("/auth/google", payload);
  return response.data;
}
