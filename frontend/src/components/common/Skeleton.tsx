import React from 'react';

export const SkeletonBox: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`animate-pulse bg-slate-800/60 rounded-xl ${className}`} />
);

export const SkeletonText: React.FC<{ lines?: number; className?: string }> = ({
  lines = 3,
  className = '',
}) => (
  <div className={`space-y-2.5 ${className}`}>
    {Array.from({ length: lines }).map((_, i) => (
      <div
        key={i}
        className="h-4 bg-slate-800/60 rounded animate-pulse"
        style={{ width: i === lines - 1 ? '60%' : '100%' }}
      />
    ))}
  </div>
);

export const ConversationSkeleton: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl mx-auto p-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="space-y-2">
          <SkeletonBox className="h-6 w-48" />
          <SkeletonBox className="h-4 w-72" />
        </div>
        <SkeletonBox className="h-8 w-24 rounded-full" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="p-6 rounded-2xl glass-panel space-y-4">
            <SkeletonBox className="h-5 w-40" />
            <SkeletonText lines={4} />
          </div>
          <div className="p-4 rounded-xl glass-panel flex gap-3 items-center">
            <SkeletonBox className="h-10 flex-1 rounded-xl" />
            <SkeletonBox className="h-10 w-20 rounded-xl" />
          </div>
        </div>

        <div className="space-y-4">
          <div className="p-5 rounded-2xl glass-panel space-y-3">
            <SkeletonBox className="h-5 w-32" />
            <SkeletonBox className="h-16 w-full rounded-lg" />
            <SkeletonBox className="h-16 w-full rounded-lg" />
            <SkeletonBox className="h-16 w-full rounded-lg" />
          </div>
        </div>
      </div>
    </div>
  );
};

export const DocumentSkeleton: React.FC = () => {
  return (
    <div className="space-y-6 max-w-6xl mx-auto p-4">
      <div className="flex justify-between items-center pb-4 border-b border-slate-800">
        <div className="space-y-2">
          <SkeletonBox className="h-7 w-56" />
          <SkeletonBox className="h-4 w-80" />
        </div>
        <SkeletonBox className="h-9 w-32 rounded-xl" />
      </div>

      <div className="p-8 border border-dashed border-slate-800 rounded-2xl flex flex-col items-center justify-center space-y-3">
        <SkeletonBox className="h-12 w-12 rounded-full" />
        <SkeletonBox className="h-5 w-48" />
        <SkeletonBox className="h-4 w-64" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="p-4 rounded-xl glass-panel space-y-3">
            <SkeletonBox className="h-5 w-36" />
            <SkeletonBox className="h-4 w-24" />
            <SkeletonText lines={2} />
          </div>
        ))}
      </div>
    </div>
  );
};

export const SummarySkeleton: React.FC = () => {
  return (
    <div className="space-y-6 max-w-5xl mx-auto p-4">
      <div className="flex justify-between items-center pb-4 border-b border-slate-800">
        <div className="space-y-2">
          <SkeletonBox className="h-7 w-64" />
          <SkeletonBox className="h-4 w-96" />
        </div>
        <SkeletonBox className="h-9 w-36 rounded-xl" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl glass-panel space-y-4">
          <SkeletonBox className="h-6 w-44" />
          <SkeletonText lines={6} />
          <SkeletonBox className="h-24 w-full rounded-xl" />
        </div>
        <div className="p-6 rounded-2xl glass-panel space-y-4">
          <SkeletonBox className="h-6 w-40" />
          <SkeletonText lines={5} />
          <div className="flex gap-3 pt-4">
            <SkeletonBox className="h-10 w-28 rounded-xl" />
            <SkeletonBox className="h-10 w-28 rounded-xl" />
          </div>
        </div>
      </div>
    </div>
  );
};
