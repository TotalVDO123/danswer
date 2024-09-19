import React, { useState, useEffect } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { FileDescriptor } from "@/app/chat/interfaces";
import { WarningCircle } from "@phosphor-icons/react";

interface CSVData {
  [key: string]: string;
}

export interface ToolDisplay {
  fileDescriptor: FileDescriptor;
  isLoading: boolean;
  fadeIn: boolean;
}

export const CsvContent = ({
  fileDescriptor,
  isLoading,
  fadeIn,
}: ToolDisplay) => {
  const [data, setData] = useState<CSVData[]>([]);
  const [headers, setHeaders] = useState<string[]>([]);
  useEffect(() => {
    fetchCSV(fileDescriptor.id);
  }, [fileDescriptor.id]);

  const fetchCSV = async (id: string) => {
    try {
      const response = await fetch(`api/chat/file/${id}`);
      if (!response.ok) {
        throw new Error("Failed to fetch CSV file");
      }

      const contentLength = response.headers.get("Content-Length");
      const fileSizeInMB = contentLength
        ? parseInt(contentLength) / (1024 * 1024)
        : 0;
      const MAX_FILE_SIZE_MB = 5;

      if (fileSizeInMB > MAX_FILE_SIZE_MB) {
        throw new Error("File size exceeds the maximum limit of 5MB");
      }

      const csvData = await response.text();
      const rows = csvData.trim().split("\n");
      const parsedHeaders = rows[0].split(",");
      setHeaders(parsedHeaders);

      const parsedData: CSVData[] = rows.slice(1).map((row) => {
        const values = row.split(",");
        return parsedHeaders.reduce<CSVData>((obj, header, index) => {
          obj[header] = values[index];
          return obj;
        }, {});
      });
      setData(parsedData);
    } catch (error) {
      console.error("Error fetching CSV file:", error);
      setData([]);
      setHeaders([]);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[300px]">
        <div className="animate-pulse w- flex space-x-4">
          <div className="rounded-full bg-background-200 h-10 w-10"></div>
          <div className="w-full flex-1 space-y-4 py-1">
            <div className="h-2 w-full bg-background-200 rounded"></div>
            <div className="w-full space-y-3">
              <div className="grid grid-cols-3 gap-4">
                <div className="h-2 bg-background-200 rounded col-span-2"></div>
                <div className="h-2 bg-background-200 rounded col-span-1"></div>
              </div>
              <div className="h-2 bg-background-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`transition-opacity transform relative duration-1000 ease-in-out ${fadeIn ? "opacity-100" : "opacity-0"}`}
    >
      <div className={`overflow-y-auto flex relative max-h-[400px]`}>
        <Table className="!relative !overflow-y-scroll">
          <TableHeader className="z-20 !sticky !top-0">
            <TableRow className="!bg-neutral-100">
              {headers.map((header, index) => (
                <TableHead className=" " key={index}>
                  <p className="text-text-600 line-clamp-2 my-2 font-medium">
                    {index === 0 ? "" : header}
                  </p>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>

          <TableBody>
            {data.length > 0 ? (
              data.map((row, rowIndex) => (
                <TableRow key={rowIndex}>
                  {headers.map((header, cellIndex) => (
                    <TableCell
                      className={`${
                        cellIndex === 0 && "sticky left-0 !bg-neutral-100"
                      }`}
                      key={cellIndex}
                    >
                      {row[header]}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={headers.length}
                  className="text-center py-8"
                >
                  <div className="flex flex-col items-center justify-center space-y-2">
                    <WarningCircle className="w-8 h-8 text-error" />
                    <p className="text-text-600 font-medium">
                      {headers.length === 0
                        ? "Error loading CSV"
                        : "No data available"}
                    </p>
                    <p className="text-text-400 text-sm">
                      {headers.length === 0
                        ? "The CSV file may be too large or couldn't be loaded properly."
                        : "The CSV file appears to be empty."}
                    </p>
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};
