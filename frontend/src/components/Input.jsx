export default function Input({
  label,
  error,
  className = "",
  inputClassName = "",
  type = "text",
  ...props
}) {
  return (
    <label className={`ui-field ${className}`}>
      {label ? (
        <span className="ui-field__label">{label}</span>
      ) : null}
      <input
        type={type}
        className={`ui-field__input ${inputClassName}`}
        {...props}
      />
      {error ? <p className="ui-field__error">{error}</p> : null}
    </label>
  );
}