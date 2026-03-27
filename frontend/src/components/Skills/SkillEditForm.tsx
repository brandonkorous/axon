import { TagInput } from "../Plugins/TagInput";

const CATEGORIES = ["general", "research", "analysis", "engineering", "communication", "planning"];

export interface SkillEditFormProps {
  description: string; setDescription: (v: string) => void;
  version: string; setVersion: (v: string) => void;
  author: string; setAuthor: (v: string) => void;
  category: string; setCategory: (v: string) => void;
  icon: string; setIcon: (v: string) => void;
  autoInject: boolean; setAutoInject: (v: boolean) => void;
  triggers: string[]; setTriggers: (v: string[]) => void;
  methodology: string; setMethodology: (v: string) => void;
}

export function SkillEditForm({
  description, setDescription, version, setVersion, author, setAuthor,
  category, setCategory, icon, setIcon, autoInject, setAutoInject,
  triggers, setTriggers, methodology, setMethodology,
}: SkillEditFormProps) {
  return (
    <div className="space-y-5">
      <label className="form-control">
        <span className="label-text text-xs mb-1">Description</span>
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} className="textarea textarea-sm textarea-bordered w-full resize-y" />
      </label>
      <div className="grid grid-cols-2 gap-3">
        <label className="form-control">
          <span className="label-text text-xs mb-1">Version</span>
          <input type="text" value={version} onChange={(e) => setVersion(e.target.value)} className="input input-sm input-bordered w-full" />
        </label>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Author</span>
          <input type="text" value={author} onChange={(e) => setAuthor(e.target.value)} className="input input-sm input-bordered w-full" />
        </label>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <label className="form-control">
          <span className="label-text text-xs mb-1">Category</span>
          <select value={category} onChange={(e) => setCategory(e.target.value)} className="select select-sm select-bordered w-full">
            {CATEGORIES.map((c) => (<option key={c} value={c}>{c}</option>))}
          </select>
        </label>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Icon</span>
          <input type="text" value={icon} onChange={(e) => setIcon(e.target.value)} className="input input-sm input-bordered w-full" />
        </label>
      </div>
      <label className="flex items-center gap-3 cursor-pointer">
        <input type="checkbox" className="toggle toggle-sm toggle-primary" checked={autoInject} onChange={(e) => setAutoInject(e.target.checked)} />
        <div>
          <span className="text-sm">Auto-inject</span>
          <p className="text-xs text-base-content/60">Always inject this skill's methodology into the agent prompt</p>
        </div>
      </label>
      <label className="form-control">
        <span className="label-text text-xs mb-1">Trigger Keywords</span>
        <TagInput tags={triggers} onChange={setTriggers} placeholder="Add keyword and press Enter" />
      </label>
      <label className="form-control">
        <span className="label-text text-xs mb-1">Methodology</span>
        <textarea value={methodology} onChange={(e) => setMethodology(e.target.value)} rows={12} className="textarea textarea-sm textarea-bordered w-full resize-y font-mono text-sm" />
      </label>
    </div>
  );
}
