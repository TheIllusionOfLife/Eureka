/**
 * Toast notification utility using react-toastify
 */
import { toast } from 'react-toastify';

type ToastOptions = any;

// Default toast options
const defaultOptions: ToastOptions = {
  position: "top-right",
  autoClose: 5000,
  hideProgressBar: false,
  closeOnClick: true,
  pauseOnHover: true,
  draggable: true,
  progress: undefined,
};

// Success toast
export const showSuccess = (message: string, options?: ToastOptions) => {
  toast.success(message, { ...defaultOptions, ...options });
};

// Error toast
export const showError = (message: string, options?: ToastOptions) => {
  toast.error(message, { ...defaultOptions, ...options });
};

// Info toast
export const showInfo = (message: string, options?: ToastOptions) => {
  toast.info(message, { ...defaultOptions, ...options });
};

// Warning toast
export const showWarning = (message: string, options?: ToastOptions) => {
  toast.warning(message, { ...defaultOptions, ...options });
};

// Generic toast
export const showToast = (message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info', options?: ToastOptions) => {
  const toastFunction = {
    success: showSuccess,
    error: showError,
    info: showInfo,
    warning: showWarning,
  }[type];
  
  toastFunction(message, options);
};