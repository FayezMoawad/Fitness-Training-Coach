/** Shared inline-error element for the app's forms — see
 * docs/ERROR_CONVENTIONS.md for the error-handling conventions this fits
 * into. Renders nothing when there's no error. */
export function FormError({ message }: { message: string | null }) {
  if (!message) {
    return null;
  }

  return (
    <p role="alert" className="text-sm text-red-600 dark:text-red-400">
      {message}
    </p>
  );
}
