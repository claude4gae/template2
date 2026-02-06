import * as React from "react"
import ReactQuill from "react-quill"

export function RichTextEditor({
  id,
  value,
  onChange,
  placeholder,
  modules,
  formats,
  readOnly = false,
  className = "",
  ariaLabelledby,
  ariaLabel,
}) {
  const normalizeHtml = (html) => {
    if (!html || html === "<p><br></p>") return ""
    return html
  }

  const editorRef = React.useRef(null)

  const handleChange = (html) => {
    if (!onChange || readOnly) return
    onChange(normalizeHtml(html))
  }

  React.useEffect(() => {
    if (!editorRef.current) return
    const editor = editorRef.current.getEditor?.()
    if (!editor?.root) return
    const root = editor.root

    if (id) {
      root.id = id
    } else {
      root.removeAttribute("id")
    }

    if (ariaLabelledby) {
      root.setAttribute("aria-labelledby", ariaLabelledby)
    } else {
      root.removeAttribute("aria-labelledby")
    }

    if (ariaLabel) {
      root.setAttribute("aria-label", ariaLabel)
    } else {
      root.removeAttribute("aria-label")
    }

    root.setAttribute("aria-readonly", readOnly ? "true" : "false")
  }, [id, ariaLabel, ariaLabelledby, readOnly])

  return (
    <ReactQuill
      ref={editorRef}
      theme="snow"
      value={normalizeHtml(value || "")}
      onChange={handleChange}
      modules={modules}
      formats={formats}
      placeholder={placeholder}
      readOnly={readOnly}
      className={["voc-quill", className].filter(Boolean).join(" ")}
    />
  )
}
