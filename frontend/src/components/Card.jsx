const variantMap = {
  default: "",
  glass: "ui-card--glass",
  dark: "ui-card--dark"
};

export default function Card({ children, className = "", variant = "default" }) {
  return (
    <div
      className={`ui-card ${variantMap[variant]} ${className}`}
    >
      {children}
    </div>
  );
}