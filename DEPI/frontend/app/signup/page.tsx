import AuthWaveLayout from "@/components/auth/AuthWaveLayout";
import SignupForm from "@/components/auth/SignupForm";

export const metadata = {
  title: "Create account — MedCortex",
  description: "Create your MedCortex account and start using AI-powered clinical assistance.",
};

export default function SignupPage() {
  return (
    <AuthWaveLayout
      rightTitle="Create Your Space"
      rightDescription="Build your profile once and MedCortex will shape suggestions, reminders, and conversations around your lifestyle with the same soft purple visual tone."
    >
      <SignupForm />
    </AuthWaveLayout>
  );
}
