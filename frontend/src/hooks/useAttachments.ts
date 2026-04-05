import { useState, useRef, useCallback, useEffect } from "react";
import type { Attachment } from "../stores/conversationStore";
import { orgApiPath } from "../stores/orgStore";

interface UseAttachmentsReturn {
  attachments: Attachment[];
  addFiles: (files: FileList | File[]) => void;
  removeAttachment: (index: number) => void;
  clearAttachments: () => void;
  uploading: boolean;
  uploadAttachments: (agentId: string) => Promise<Attachment[]>;
}

function isImageType(type: string): boolean {
  return type.startsWith("image/");
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export function useAttachments(): UseAttachmentsReturn {
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [uploading, setUploading] = useState(false);
  const filesRef = useRef<Map<number, File>>(new Map());
  const objectUrlsRef = useRef<string[]>([]);
  const counterRef = useRef(0);

  // Clean up object URLs on unmount
  useEffect(() => {
    return () => {
      objectUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
    };
  }, []);

  const addFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files);

    fileArray.forEach(async (file) => {
      const idx = counterRef.current++;
      filesRef.current.set(idx, file);

      let preview: string | undefined;
      if (isImageType(file.type)) {
        // Use object URL for fast local preview
        const objUrl = URL.createObjectURL(file);
        objectUrlsRef.current.push(objUrl);
        preview = objUrl;
      }

      const attachment: Attachment = {
        path: "",
        name: file.name,
        type: file.type,
        size: file.size,
        preview,
      };

      setAttachments((prev) => [...prev, attachment]);

      // For images, also read as data URL for persistence in messages
      if (isImageType(file.type)) {
        try {
          const dataUrl = await readFileAsDataUrl(file);
          setAttachments((prev) =>
            prev.map((a) =>
              a.name === file.name && a.size === file.size && a.preview === preview
                ? { ...a, preview: dataUrl }
                : a
            )
          );
        } catch {
          // Keep object URL as fallback
        }
      }
    });
  }, []);

  const removeAttachment = useCallback((index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
    filesRef.current.delete(index);
  }, []);

  const clearAttachments = useCallback(() => {
    setAttachments([]);
    filesRef.current.clear();
    objectUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
    objectUrlsRef.current = [];
  }, []);

  const uploadAttachments = useCallback(
    async (agentId: string): Promise<Attachment[]> => {
      const files = Array.from(filesRef.current.values());
      if (files.length === 0) return attachments;

      setUploading(true);
      try {
        const results = await Promise.all(
          files.map(async (file, i) => {
            const formData = new FormData();
            formData.append("file", file);

            const res = await fetch(
              orgApiPath(`conversations/${agentId}/upload`),
              { method: "POST", body: formData }
            );
            if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);
            const data = await res.json();

            return {
              ...attachments[i],
              path: data.path || data.filename || file.name,
            };
          })
        );
        return results;
      } finally {
        setUploading(false);
      }
    },
    [attachments]
  );

  return {
    attachments,
    addFiles,
    removeAttachment,
    clearAttachments,
    uploading,
    uploadAttachments,
  };
}
