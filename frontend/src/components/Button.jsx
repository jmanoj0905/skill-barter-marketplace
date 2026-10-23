const variantMap = {
	primary: "ui-btn--primary",
	secondary: "ui-btn--secondary",
	ghost: "ui-btn--ghost"
};

export default function Button({
	children,
	type = "button",
	variant = "primary",
	className = "",
	disabled,
	...props
}) {
	return (
		<button
			type={type}
			disabled={disabled}
			className={`ui-btn ${variantMap[variant]} ${className}`}
			{...props}
		>
			{children}
		</button>
	);
}
