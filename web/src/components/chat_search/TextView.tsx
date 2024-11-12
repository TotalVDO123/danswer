"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Download, Printer, ZoomIn, ZoomOut } from "lucide-react";

interface TextViewProps {
  fileUrl?: string;
  fileName?: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function TextView({
  fileUrl = "/sample.pdf",
  fileName = "Document.pdf",
  isOpen,
  onClose,
}: TextViewProps) {
  const [zoom, setZoom] = useState(100);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 25, 200));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 25, 50));

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent
        hideCloseIcon
        className="max-w-5xl w-[90vw] gap-y-0 max-h-[80vh] p-0"
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
        <div className="mt-0 flex-1 overflow-hidden">
          <div
            style={{
              overflow: "hidden",
              width: `${zoom}%`,
              height: `${zoom}%`,
              minWidth: "100%",
              minHeight: "100%",
              transition: "width 0.3s ease",
            }}
          >
            <iframe
              src={`${fileUrl}#toolbar=0`}
              className="w-full h-full border-none"
              style={{ height: "calc(80vh - 60px)" }}
              title="PDF Viewer"
            />
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// import { useState } from "react";
// import { Button } from "@/components/ui/button";
// import {
//   Dialog,
//   DialogContent,
//   DialogHeader,
//   DialogTitle,
// } from "@/components/ui/dialog";
// import { Download, Printer, ZoomIn, ZoomOut } from "lucide-react";
// import { Document, Page, pdfjs } from "react-pdf";
// import "react-pdf/dist/esm/Page/AnnotationLayer.css";
// import "react-pdf/dist/esm/Page/TextLayer.css";

// // Set up the worker for react-pdf
// pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

// interface TextViewProps {
//   fileUrl: string;
//   fileName: string;
//   fileType?: "pdf" | "txt" | "md";
//   isOpen: boolean;
//   onClose: () => void;
// }

// export default function TextView({
//   fileUrl,
//   fileName,
//   fileType = "pdf",
//   isOpen,
//   onClose,
// }: TextViewProps) {
//   pdfjs.GlobalWorkerOptions.workerSrc = new URL(
//     "pdfjs-dist/legacy/build/pdf.worker.min.mjs",
//     import.meta.url
//   ).toString();
//   const [zoom, setZoom] = useState(100);
//   const [numPages, setNumPages] = useState<number | null>(null);
//   const [pageNumber, setPageNumber] = useState(1);

//   const handleZoomIn = () => setZoom((prev) => Math.min(prev + 25, 200));
//   const handleZoomOut = () => setZoom((prev) => Math.max(prev - 25, 50));

//   function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
//     setNumPages(numPages);
//   }

//   return (
//     <Dialog open={isOpen} onOpenChange={onClose}>
//       <DialogContent
//         hideCloseIcon
//         className="max-w-5xl w-[90vw] gap-y-0 max-h-[80vh] p-0"
//       >
//         <DialogHeader className="px-4 mb-0 py-2 flex flex-row items-center justify-between border-b">
//           <DialogTitle className="text-lg font-medium truncate">
//             {fileName}
//           </DialogTitle>
//           <div className="flex items-center space-x-2">
//             {/* ... existing zoom, download, and print buttons ... */}
//             {fileType === "pdf" && (
//               <span className="text-sm">
//                 Page {pageNumber} of {numPages}
//               </span>
//             )}
//           </div>
//         </DialogHeader>
//         <div className="mt-0 flex-1 overflow-auto">
//           <div
//             style={{
//               width: `${zoom}%`,
//               height: `${zoom}%`,
//               minWidth: "100%",
//               minHeight: "100%",
//               transition: "width 0.3s ease",
//             }}
//           >
//             {fileType === "pdf" ? (
//               <Document
//                 file={fileUrl}
//                 onLoadSuccess={onDocumentLoadSuccess}
//                 className="w-full h-full"
//               >
//                 <Page
//                   pageNumber={pageNumber}
//                   width={window.innerWidth * 0.9}
//                   scale={zoom / 100}
//                 />
//               </Document>
//             ) : (
//               <iframe
//                 src={fileUrl}
//                 className="w-full h-full border-none"
//                 style={{ height: "calc(80vh - 60px)" }}
//                 title="Text Viewer"
//               />
//             )}
//           </div>
//         </div>
//         {fileType === "pdf" && (
//           <div className="flex justify-center items-center p-2 border-t">
//             <Button
//               onClick={() => setPageNumber((prev) => Math.max(prev - 1, 1))}
//               disabled={pageNumber <= 1}
//             >
//               Previous
//             </Button>
//             <span className="mx-4">
//               Page {pageNumber} of {numPages}
//             </span>
//             <Button
//               onClick={() =>
//                 setPageNumber((prev) => Math.min(prev + 1, numPages || 1))
//               }
//               disabled={pageNumber >= (numPages || 1)}
//             >
//               Next
//             </Button>
//           </div>
//         )}
//       </DialogContent>
//     </Dialog>
//   );
// }
