import AuthWaveLayout from "@/components/auth/AuthWaveLayout";
import LoginForm from "@/components/auth/LoginForm";

export const metadata = {
  title: "Sign in — MedCortex",
  description: "Sign in to your MedCortex AI health assistant account.",
};

export default function LoginPage() {
  return (
    <AuthWaveLayout
      rightTitle="Welcome Back!"
      rightDescription="Track your health journey, chat with your AI assistant, and pick up exactly where you left off in a calmer, lighter MedCortex experience."
    >
      <LoginForm />
    </AuthWaveLayout>
  );
}
