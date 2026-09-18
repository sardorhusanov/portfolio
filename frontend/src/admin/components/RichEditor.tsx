import { useRef, useState } from "react";
import { EditorContent, useEditor, useEditorState } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Image from "@tiptap/extension-image";
import Placeholder from "@tiptap/extension-placeholder";
import { TableKit } from "@tiptap/extension-table";
import {
  Bold,
  Italic,
  Strikethrough,
  Code,
  List,
  ListOrdered,
  Quote,
  Link as LinkIcon,
  ImagePlus,
  Minus,
  Undo,
  Redo,
  Table,
} from "lucide-react";
import type { EditorNode } from "../../types/admin";
import { adminApi } from "../../api/admin";
import { ErrorNotice } from "./Common";
export function RichEditor({
  initial,
  onChange,
  onBusy,
}: {
  initial: EditorNode | string;
  onBusy?: (busy: boolean) => void;
  onChange: (json: EditorNode, words: number) => void;
}) {
  const [error, setError] = useState<unknown>(null);
  const [uploading, setUploading] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
        link: { openOnClick: false },
      }),
      Image.configure({ allowBase64: false }),
      Placeholder.configure({ placeholder: "Start with an idea…" }),
      TableKit,
    ],
    content: initial,
    editorProps: {
      attributes: {
        class: "prose editor-prose",
        "aria-label": "Article content",
        role: "textbox",
        "aria-multiline": "true",
      },
      handlePaste: (_view, event) => {
        const file = Array.from(event.clipboardData?.files || []).find((file) =>
          file.type.startsWith("image/"),
        );
        if (file) {
          void insertImage(file);
          return true;
        }
        return false;
      },
      handleDrop: (_view, event) => {
        const file = Array.from(event.dataTransfer?.files || []).find((file) =>
          file.type.startsWith("image/"),
        );
        if (file) {
          event.preventDefault();
          void insertImage(file);
          return true;
        }
        return false;
      },
    },
    onCreate: ({ editor: instance }) => {
      if (typeof initial === "string")
        onChange(
          instance.getJSON() as EditorNode,
          instance.getText().trim().split(/\s+/).filter(Boolean).length,
        );
    },
    onUpdate: ({ editor: instance }) =>
      onChange(
        instance.getJSON() as EditorNode,
        instance.getText().trim().split(/\s+/).filter(Boolean).length,
      ),
  });
  useEditorState({
    editor,
    selector: ({ editor: value }) => ({
      selection: value?.state.selection.from,
      size: value?.state.doc.content.size,
      marks: [
        "bold",
        "italic",
        "strike",
        "code",
        "heading",
        "codeBlock",
        "bulletList",
        "orderedList",
        "blockquote",
        "table",
      ].map((name) => value?.isActive(name)),
      heading: value?.getAttributes("heading").level,
      undo: value?.can().undo(),
      redo: value?.can().redo(),
    }),
  });
  async function insertImage(file: File) {
    if (!editor) return;
    const alt = window.prompt(
      "Describe this image for readers using a screen reader:",
      "",
    );
    if (alt === null) return;
    setUploading(true);
    onBusy?.(true);
    setError(null);
    try {
      const result = await adminApi.upload(file, "posts");
      editor.chain().focus().setImage({ src: result.url, alt }).run();
    } catch (e) {
      setError(e);
    } finally {
      setUploading(false);
      onBusy?.(false);
    }
  }
  if (!editor) return <div className="skeleton">Opening editor…</div>;
  const tools = [
    {
      label: "Bold",
      Icon: Bold,
      active: editor.isActive("bold"),
      run: () => editor.chain().focus().toggleBold().run(),
    },
    {
      label: "Italic",
      Icon: Italic,
      active: editor.isActive("italic"),
      run: () => editor.chain().focus().toggleItalic().run(),
    },
    {
      label: "Strike",
      Icon: Strikethrough,
      active: editor.isActive("strike"),
      run: () => editor.chain().focus().toggleStrike().run(),
    },
    {
      label: "Inline code",
      Icon: Code,
      active: editor.isActive("code"),
      run: () => editor.chain().focus().toggleCode().run(),
    },
    {
      label: "Bullet list",
      Icon: List,
      active: editor.isActive("bulletList"),
      run: () => editor.chain().focus().toggleBulletList().run(),
    },
    {
      label: "Numbered list",
      Icon: ListOrdered,
      active: editor.isActive("orderedList"),
      run: () => editor.chain().focus().toggleOrderedList().run(),
    },
    {
      label: "Quote",
      Icon: Quote,
      active: editor.isActive("blockquote"),
      run: () => editor.chain().focus().toggleBlockquote().run(),
    },
  ];
  return (
    <div className="rich-editor">
      <div className="editor-toolbar" role="toolbar" aria-label="Formatting">
        <select
          aria-label="Text style"
          value={
            editor.isActive("heading")
              ? `h${editor.getAttributes("heading").level}`
              : editor.isActive("codeBlock")
                ? "code"
                : "paragraph"
          }
          onChange={(event) => {
            const value = event.target.value;
            if (value === "paragraph")
              editor.chain().focus().setParagraph().run();
            else if (value === "code")
              editor.chain().focus().toggleCodeBlock().run();
            else
              editor
                .chain()
                .focus()
                .toggleHeading({ level: Number(value.slice(1)) as 1 | 2 | 3 })
                .run();
          }}
        >
          <option value="paragraph">Paragraph</option>
          <option value="h1">Heading 1</option>
          <option value="h2">Heading 2</option>
          <option value="h3">Heading 3</option>
          <option value="code">Code block</option>
        </select>
        {tools.map(({ label, Icon, active, run }) => (
          <button
            key={label}
            type="button"
            title={label}
            aria-label={label}
            aria-pressed={active}
            onClick={run}
          >
            <Icon size={16} />
          </button>
        ))}
        <button
          type="button"
          aria-label="Edit link"
          title="Edit link"
          onClick={() => {
            const url = window.prompt(
              "Link URL (leave empty to remove):",
              editor.getAttributes("link").href || "",
            );
            if (url === null) return;
            if (!url.trim()) editor.chain().focus().unsetLink().run();
            else if (/^(https?:\/\/|mailto:|\/(?!\/))/.test(url))
              editor
                .chain()
                .focus()
                .extendMarkRange("link")
                .setLink({ href: url })
                .run();
            else setError(new Error("Use an HTTP(S) or mailto URL."));
          }}
        >
          <LinkIcon size={16} />
        </button>
        <button
          type="button"
          aria-label="Insert image"
          title="Insert image"
          disabled={uploading}
          onClick={() => fileInput.current?.click()}
        >
          <ImagePlus size={16} />
        </button>
        <button
          type="button"
          aria-label="Horizontal rule"
          title="Horizontal rule"
          onClick={() => editor.chain().focus().setHorizontalRule().run()}
        >
          <Minus size={16} />
        </button>
        <button
          type="button"
          aria-label="Insert table"
          title="Insert table"
          onClick={() =>
            editor
              .chain()
              .focus()
              .insertTable({ rows: 3, cols: 3, withHeaderRow: true })
              .run()
          }
        >
          <Table size={16} />
        </button>
        <button
          type="button"
          aria-label="Undo"
          title="Undo"
          disabled={!editor.can().undo()}
          onClick={() => editor.chain().focus().undo().run()}
        >
          <Undo size={16} />
        </button>
        <button
          type="button"
          aria-label="Redo"
          title="Redo"
          disabled={!editor.can().redo()}
          onClick={() => editor.chain().focus().redo().run()}
        >
          <Redo size={16} />
        </button>
      </div>
      {editor.isActive("codeBlock") && (
        <label className="code-language">
          Language{" "}
          <select
            value={editor.getAttributes("codeBlock").language || "plaintext"}
            onChange={(e) =>
              editor
                .chain()
                .focus()
                .updateAttributes("codeBlock", { language: e.target.value })
                .run()
            }
          >
            {["plaintext", "python", "sql", "javascript", "bash"].map(
              (language) => (
                <option key={language}>{language}</option>
              ),
            )}
          </select>
        </label>
      )}
      {editor.isActive("table") && (
        <div className="table-actions">
          <button onClick={() => editor.chain().focus().addRowAfter().run()}>
            Add row
          </button>
          <button onClick={() => editor.chain().focus().addColumnAfter().run()}>
            Add column
          </button>
          <button onClick={() => editor.chain().focus().deleteTable().run()}>
            Remove table
          </button>
        </div>
      )}
      <input
        ref={fileInput}
        hidden
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) void insertImage(file);
          event.target.value = "";
        }}
      />
      <ErrorNotice error={error} />
      {uploading && (
        <p role="status" className="help-text">
          Uploading image…
        </p>
      )}
      <EditorContent editor={editor} />
    </div>
  );
}
