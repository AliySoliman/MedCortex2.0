export type User = {
  id: number;
  name: string;
  email: string;
  age?: number | null;
  gender?: string | null;
  activity_level?: string | null;
  allergies?: string | null;
  conditions?: string | null;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type SignupPayload = LoginPayload & {
  name: string;
  age?: number;
  gender?: string;
  activity_level?: "low" | "medium" | "high";
  allergies?: string;
  conditions?: string;
};

export type GoogleAuthPayload = {
  id_token: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  user: User;
};
