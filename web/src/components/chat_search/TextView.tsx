"use client";

import { useState, useEffect, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Download, Printer, ZoomIn, ZoomOut } from "lucide-react";

interface TextViewProps {
  fileUrl: string;
  fileName: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function TextView({
  fileUrl,
  fileName,
  isOpen,
  onClose,
}: TextViewProps) {
  const [zoom, setZoom] = useState(100);
  const [markdownContent, setMarkdownContent] = useState<string>("");

  const fileType = useMemo(() => {
    const extension = fileName.split(".").pop()?.toLowerCase();
    switch (extension) {
      case "md":
      case "markdown":
        return "text/markdown";
      case "pdf":
        return "application/pdf";
      case "docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
      default:
        return "application/octet-stream";
    }
  }, [fileName]);

  useEffect(() => {
    if (fileType === "text/markdown") {
      fetch(fileUrl)
        .then((response) => response.text())
        .then((text) => setMarkdownContent(text))
        .catch((error) =>
          console.error("Error fetching Markdown content:", error)
        );
    }
  }, [fileUrl, fileType]);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 25, 200));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 25, 50));

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent
        hideCloseIcon
        className="max-w-5xl w-[90vw] flex flex-col justify-between gap-y-0 max-h-[80vh] p-0"
      >
        <DialogHeader className="px-4 mb-0 py-2 flex flex-row items-center justify-between border-b">
          <DialogTitle className="text-lg font-medium truncate">
            {fileName}
          </DialogTitle>
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="icon" onClick={handleZoomOut}>
              <ZoomOut className="h-4 w-4" />
              <span className="sr-only">Zoom Out</span>
            </Button>
            <span className="text-sm">{zoom}%</span>
            <Button variant="ghost" size="icon" onClick={handleZoomIn}>
              <ZoomIn className="h-4 w-4" />
              <span className="sr-only">Zoom In</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => window.open(fileUrl, "_blank")}
            >
              <Download className="h-4 w-4" />
              <span className="sr-only">Download</span>
            </Button>
            <Button variant="ghost" size="icon" onClick={() => window.print()}>
              <Printer className="h-4 w-4" />
              <span className="sr-only">Print</span>
            </Button>
          </div>
        </DialogHeader>
        <div className="mt-0 rounded-b-lg flex-1 overflow-hidden">
          <div
            style={{
              width: `${zoom}%`,
              height: `${zoom}%`,
              minWidth: "100%",
              minHeight: "100%",
              transition: "width 0.3s ease",
            }}
          >
            {fileType === "application/pdf" ? (
              <iframe
                src={`${fileUrl}#toolbar=0`}
                className="w-full h-full border-none"
                style={{ height: "calc(80vh - 60px)" }}
                title="PDF Viewer"
              />
            ) : fileType === "text/markdown" ? (
              <div
                className="p-4 overflow-auto"
                style={{ height: "calc(80vh - 60px)" }}
              >
                <ReactMarkdown>{markdownContent}</ReactMarkdown>
              </div>
            ) : (
              <iframe
                src={fileUrl}
                className="w-full h-full border-none"
                style={{ height: "calc(80vh - 60px)" }}
                title="File Viewer"
              />
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
