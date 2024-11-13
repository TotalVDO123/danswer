"use client";

import { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Download, XIcon, ZoomIn, ZoomOut } from "lucide-react";
import { DanswerDocument } from "@/lib/search/interfaces";
import { MinimalMarkdown } from "./MinimalMarkdown";

interface TextViewProps {
  presentingDocument: DanswerDocument;
  onClose: () => void;
}

export default function TextView({
  presentingDocument,
  onClose,
}: TextViewProps) {
  const [zoom, setZoom] = useState(100);
  const [fileContent, setFileContent] = useState<string>("");
  const [fileUrl, setFileUrl] = useState<string>("");
  const [fileName, setFileName] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchFile = async () => {
      setIsLoading(true);
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

        if (blob.type === "text/markdown" || blob.type === "text/plain") {
          const text = await blob.text();
          setFileContent(text);
        }
      } catch (error) {
        console.error("Error fetching file:", error);
      } finally {
        setTimeout(() => {
          setIsLoading(false);
        }, 1000);
      }
    };

    fetchFile();
  }, [presentingDocument]);

  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = fileUrl;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 25, 200));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 25, 100));

  return (
    <Dialog open={true} onOpenChange={onClose}>
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
              <span className="sr-only">Close</span>
            </Button>
          </div>
        </DialogHeader>
        <div className="mt-0 rounded-b-lg flex-1 overflow-hidden">
          <div className="flex items-center justify-center w-full h-full">
            {isLoading ? (
              <div className="text-center items-center flex flex-col">
                <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-neutral-800"></div>
                <p className="mt-4 text-xl font-medium">Loading document...</p>
              </div>
            ) : (
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
                    className="w-full p-6 overflow-y-scroll overflow-x-hidden"
                    style={{ height: "100%" }}
                  >
                    <MinimalMarkdown
                      content={fileContent}
                      className="w-full pb-4 h-full text-lg text-wrap break-words"
                    />
                  </div>
                ) : (
                  <iframe
                    src={fileUrl}
                    className="w-full h-full border-none"
                    title="File Viewer"
                  />
                )}
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
