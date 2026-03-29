import { useEffect, useState } from "react";
import { useSandboxStore, type SandboxImageInfo } from "../../stores/sandboxStore";
import { SandboxImageCard } from "./SandboxImageCard";
import { SandboxBuildDialog } from "./SandboxBuildDialog";

/** Group images into a tree by parent_type for display ordering. */
function buildImageTree(images: SandboxImageInfo[]): SandboxImageInfo[] {
  const byType = new Map(images.map((img) => [img.type, img]));
  const roots: SandboxImageInfo[] = [];
  const children = new Map<string, SandboxImageInfo[]>();

  for (const img of images) {
    if (!img.parent_type || !byType.has(img.parent_type)) {
      roots.push(img);
    } else {
      const list = children.get(img.parent_type) || [];
      list.push(img);
      children.set(img.parent_type, list);
    }
  }

  // Flatten tree: root, then its children, recursively
  const result: SandboxImageInfo[] = [];
  const visit = (node: SandboxImageInfo, depth = 0) => {
    result.push(node);
    const kids = children.get(node.type) || [];
    for (const kid of kids) visit(kid, depth + 1);
  };
  for (const root of roots) visit(root);
  return result;
}

export function SandboxImagesView() {
  const { images, loading, fetchImages, removeImage } = useSandboxStore();
  const [buildTarget, setBuildTarget] = useState<SandboxImageInfo | null>(null);
  const [confirmRemove, setConfirmRemove] = useState<string | null>(null);

  useEffect(() => {
    fetchImages();
    const interval = setInterval(fetchImages, 15_000);
    return () => clearInterval(interval);
  }, [fetchImages]);

  const orderedImages = buildImageTree(images);

  const handleRemove = async (type: string) => {
    await removeImage(type);
    setConfirmRemove(null);
    fetchImages();
  };

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-neutral">
        <h1 className="text-xl font-bold text-base-content">Sandboxes</h1>
        <p className="text-xs text-base-content/60 mt-1">
          Container images for isolated agent execution environments
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {loading && images.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <span className="loading loading-spinner loading-md text-primary" />
          </div>
        ) : images.length === 0 ? (
          <p className="text-sm text-base-content/60 text-center mt-12">
            No sandbox images configured
          </p>
        ) : (
          <div className="max-w-2xl mx-auto space-y-3">
            {orderedImages.map((image) => (
              <div key={image.type}>
                <SandboxImageCard
                  image={image}
                  onBuild={() => setBuildTarget(image)}
                  onRemove={() => setConfirmRemove(image.type)}
                />

                {/* Inline remove confirmation */}
                {confirmRemove === image.type && (
                  <div className="flex items-center gap-2 mt-1 ml-4">
                    <span className="text-xs text-error">Remove this image?</span>
                    <button
                      onClick={() => handleRemove(image.type)}
                      className="btn btn-error btn-xs"
                    >
                      Yes, remove
                    </button>
                    <button
                      onClick={() => setConfirmRemove(null)}
                      className="btn btn-ghost btn-xs"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {buildTarget && (
        <SandboxBuildDialog
          image={buildTarget}
          onClose={() => {
            setBuildTarget(null);
            fetchImages();
          }}
        />
      )}
    </div>
  );
}
