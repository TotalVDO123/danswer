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
import { Download, XIcon, ZoomIn, ZoomOut } from "lucide-react";
import { DanswerDocument } from "@/lib/search/interfaces";

interface TextViewProps {
  presentingDocument: DanswerDocument;
  isOpen: boolean;
  onClose: () => void;
}

export default function TextView({
  presentingDocument,
  isOpen,
  onClose,
}: TextViewProps) {
  const [zoom, setZoom] = useState(100);
  const [markdownContent, setMarkdownContent] = useState<string>("");

  const [fileUrl, setFileUrl] = useState<string>("");
  const [fileName, setFileName] = useState<string>("");

  useEffect(() => {
    const fetchFile = async () => {
      const fileId = presentingDocument.document_id.split("__")[1];
      try {
        const response = await fetch(
          `/api/query/file?file_id=${encodeURIComponent(fileId)}`,
          {
            method: "GET",
          }
        );
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        setFileUrl(url);
        setFileName(presentingDocument.semantic_identifier || "document");
      } catch (error) {
        console.error("Error fetching file:", error);
      }
    };

    fetchFile();
  }, [document]);

  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = fileUrl;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handlePrint = () => {
    const printWindow = window.open(fileUrl, "_blank");
    printWindow?.print();
  };

  const fileType = useMemo(() => {
    const extension = fileName
      ? fileName.split(".").pop()?.toLowerCase()
      : "md";
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
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 25, 100));

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent
        hideCloseIcon
        className="max-w-5xl w-[90vw] flex flex-col justify-between gap-y-0 h-full max-h-[80vh] p-0"
      >
        <DialogHeader className="px-4 mb-0 pt-2 pb-3 flex flex-row items-center justify-between border-b">
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
            <Button variant="ghost" size="icon" onClick={handleDownload}>
              <Download className="h-4 w-4" />
              <span className="sr-only">Download</span>
            </Button>
            <Button variant="ghost" size="icon" onClick={() => onClose()}>
              <XIcon className="h-4 w-4" />
              <span className="sr-only">Print</span>
            </Button>
          </div>
        </DialogHeader>
        <div className="mt-0 rounded-b-lg flex-1 overflow-hidden">
          <div className="flex items-center justify-center w-full h-full">
            <div
              style={{
                transform: `scale(${zoom / 100})`,
                transformOrigin: "center center",
                transition: "transform 0.3s ease",
                width: "100%",
                height: "100%",
              }}
            >
              {fileType === "application/pdf" ? (
                <iframe
                  src={`${fileUrl}#toolbar=0`}
                  className="w-full h-full border-none"
                  title="PDF Viewer"
                />
              ) : fileType === "text/markdown" ? (
                <div
                  className="p-8 overflow-auto overflow-x-hidden"
                  style={{ height: "100%" }}
                >
                  <ReactMarkdown>{markdownContent}</ReactMarkdown>
                </div>
              ) : (
                <iframe
                  src={fileUrl}
                  className="w-full h-full border-none"
                  title="File Viewer"
                />
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
