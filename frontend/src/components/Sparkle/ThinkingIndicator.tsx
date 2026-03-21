import { motion } from "framer-motion";

interface Props {
  color?: string;
  agentName?: string;
}

export function ThinkingIndicator({ color = "#8B5CF6", agentName = "Axon" }: Props) {
  return (
    <div className="flex items-center gap-3 px-4 py-3">
      <motion.div
        className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white"
        style={{ backgroundColor: color }}
        animate={{
          boxShadow: [
            `0 0 0 0 ${color}40`,
            `0 0 0 12px ${color}00`,
            `0 0 0 0 ${color}40`,
          ],
        }}
        transition={{ duration: 1.5, repeat: Infinity }}
      >
        {agentName[0]}
      </motion.div>
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: color }}
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
          />
        ))}
      </div>
      <span className="text-sm text-gray-500">{agentName} is thinking...</span>
    </div>
  );
}
