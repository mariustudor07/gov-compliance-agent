import useReveal from "../hooks/useReveal";

/** Fades/slides children in once they scroll into view. `delay` in ms for
 * staggering a list of these. */
export default function Reveal({ children, delay = 0, as: Tag = "div", className = "", style }) {
  const [ref, visible] = useReveal();
  return (
    <Tag
      ref={ref}
      className={`reveal ${visible ? "reveal--visible" : ""} ${className}`}
      style={{ ...style, transitionDelay: visible ? `${delay}ms` : "0ms" }}
    >
      {children}
    </Tag>
  );
}
