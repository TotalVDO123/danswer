import { Citation } from "@/components/search/results/Citation";
import React, { memo } from "react";

export const MemoizedLink = memo(
  ({ node, updatePresentingDocument, ...rest }: any) => {
    const value = rest.children;

    if (value?.toString().startsWith("*")) {
      return (
        <div className="flex-none bg-background-800 inline-block rounded-full h-3 w-3 ml-2" />
      );
    }

    if (value?.toString().startsWith("[")) {
      return (
        <Citation
          link={rest?.href}
          updatePresentingDocument={updatePresentingDocument}
        >
          {rest.children}
        </Citation>
      );
    }

    return (
      <a
        onMouseDown={() => rest.href && window.open(rest.href, "_blank")}
        className="cursor-pointer text-link hover:text-link-hover"
      >
        {rest.children}
      </a>
    );
  }
);

export const MemoizedParagraph = memo(({ ...props }: any) => (
  <p {...props} className="text-default text-text-900" />
));

MemoizedLink.displayName = "MemoizedLink";
MemoizedParagraph.displayName = "MemoizedParagraph";
