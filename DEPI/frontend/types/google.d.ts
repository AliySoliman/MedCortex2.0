type GoogleCredentialResponse = {
  credential: string;
  select_by: string;
};

type GooglePromptMomentNotification = {
  isDisplayMoment: () => boolean;
  isDisplayed: () => boolean;
  isNotDisplayed: () => boolean;
  getNotDisplayedReason: () => string;
  isSkippedMoment: () => boolean;
  getSkippedReason: () => string;
  isDismissedMoment: () => boolean;
  getDismissedReason: () => string;
};

type GoogleIdConfiguration = {
  client_id: string;
  callback: (response: GoogleCredentialResponse) => void;
};

type GoogleAccounts = {
  id: {
    cancel: () => void;
    initialize: (config: GoogleIdConfiguration) => void;
    prompt: (
      momentListener?: (notification: GooglePromptMomentNotification) => void,
    ) => void;
  };
};

declare global {
  interface Window {
    google?: {
      accounts: GoogleAccounts;
    };
  }
}

export {};
