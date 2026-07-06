export type DoctorReferral = {
  specialist: string;
  urgency: "routine" | "soon" | "urgent";
  reason: string;
};

const REFERRAL_BLOCK_REGEX = /\[DOCTOR_REFERRAL\]([\s\S]*?)\[\/DOCTOR_REFERRAL\]/;

export function extractDoctorReferral(
  text: string,
): { referral: DoctorReferral | null; cleanText: string } {
  const match = text.match(REFERRAL_BLOCK_REGEX);

  if (!match) {
    return { referral: null, cleanText: text };
  }

  try {
    const parsed = JSON.parse(match[1].trim()) as Partial<DoctorReferral>;

    if (
      typeof parsed.specialist !== "string" ||
      typeof parsed.urgency !== "string" ||
      typeof parsed.reason !== "string" ||
      !["routine", "soon", "urgent"].includes(parsed.urgency)
    ) {
      return { referral: null, cleanText: text };
    }

    const cleanText = text.replace(REFERRAL_BLOCK_REGEX, "").trim();

    return {
      referral: {
        specialist: parsed.specialist,
        urgency: parsed.urgency,
        reason: parsed.reason,
      },
      cleanText,
    };
  } catch {
    return { referral: null, cleanText: text };
  }
}
