import { useEffect, useRef, useState } from "react";

/** Animates a number from 0 to `value` over `duration` ms, using an
 * ease-out curve. Used for score rings/tiles so numbers feel alive. */
export default function useCountUp(value, duration = 900) {
  const [display, setDisplay] = useState(0);
  const frame = useRef(null);

  useEffect(() => {
    const target = typeof value === "number" ? value : 0;
    const start = performance.now();

    function tick(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setDisplay(Math.round(target * eased));
      if (progress < 1) frame.current = requestAnimationFrame(tick);
    }

    frame.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame.current);
  }, [value, duration]);

  return display;
}
