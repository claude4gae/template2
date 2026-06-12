import { forwardRef } from "react"
import { Link } from "react-router-dom"

import { cn } from "@/lib/utils"

function isExternalHref(href) {
  if (!href) return false
  return (
    href.startsWith("http://") ||
    href.startsWith("https://") ||
    href.startsWith("//") ||
    href.startsWith("mailto:") ||
    href.startsWith("tel:") ||
    href.startsWith("#")
  )
}

export const PortalNavLink = forwardRef(function PortalNavLink(
  { href, className, onNavigate, children, target, rel, ...props },
  ref,
) {
  const handleNavigate = (event) => {
    onNavigate?.(event)
  }

  if (!href || isExternalHref(href)) {
    const externalRel = target === "_blank" ? rel ?? "noreferrer" : rel
    return (
      <a
        ref={ref}
        href={href || "#"}
        className={className}
        onClick={handleNavigate}
        target={target}
        rel={externalRel}
        {...props}
      >
        {children}
      </a>
    )
  }

  return (
    <Link
      ref={ref}
      to={href}
      className={cn(className)}
      onClick={handleNavigate}
      {...props}
    >
      {children}
    </Link>
  )
})
