import {
  Box,
  Button,
  Paper,
  Typography
} from "@mui/material";
import { CloudUpload } from "@mui/icons-material";
import React, { useCallback, useState } from "react";

interface FileUploadZoneProps {
  onFileSelect: (file: File) => void;
  acceptedTypes?: string;
  maxSizeMB?: number;
}

const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  onFileSelect,
  acceptedTypes = ".docx,.doc,.pdf",
  maxSizeMB = 10,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateFile = (file: File): boolean => {
    setError(null);

    // Check file type
    const validExtensions = acceptedTypes.split(",").map((ext) => ext.trim());
    const fileExtension = "." + file.name.split(".").pop()?.toLowerCase();
    if (!validExtensions.includes(fileExtension)) {
      setError(`Invalid file type. Accepted: ${acceptedTypes}`);
      return false;
    }

    // Check file size
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setError(`File too large. Maximum size: ${maxSizeMB}MB`);
      return false;
    }

    return true;
  };

  const handleFile = useCallback(
    (file: File) => {
      if (validateFile(file)) {
        onFileSelect(file);
      }
    },
    [onFileSelect, acceptedTypes, maxSizeMB]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        handleFile(files[0]);
      }
    },
    [handleFile]
  );

  const handleFileInputChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ): void => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  return (
    <Box>
      <Paper
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        sx={{
          p: { xs: 2, sm: 4 },
          border: 2,
          borderStyle: "dashed",
          borderColor: isDragging ? "primary.main" : "grey.300",
          backgroundColor: isDragging ? "action.hover" : "background.paper",
          textAlign: "center",
          cursor: "pointer",
          transition: "all 0.2s ease-in-out",
          "&:hover": {
            borderColor: "primary.main",
            backgroundColor: "action.hover",
          },
        }}
      >
        <input
          type="file"
          accept={acceptedTypes}
          onChange={handleFileInputChange}
          style={{ display: "none" }}
          id="file-upload-input"
        />
        <label htmlFor="file-upload-input" style={{ cursor: "pointer" }}>
          <CloudUpload 
            sx={{ 
              fontSize: { xs: 36, sm: 48 }, 
              color: "primary.main", 
              mb: { xs: 1, sm: 2 } 
            }} 
          />
          <Typography 
            variant="h6" 
            gutterBottom
            sx={{ fontSize: { xs: "1rem", sm: "1.25rem" } }}
          >
            {isDragging
              ? "Drop file here"
              : "Drag and drop resume file here"}
          </Typography>
          <Typography 
            variant="body2" 
            color="text.secondary" 
            gutterBottom
            sx={{ fontSize: { xs: "0.75rem", sm: "0.875rem" } }}
          >
            or click to browse
          </Typography>
          <Typography 
            variant="caption" 
            color="text.secondary" 
            display="block" 
            sx={{ 
              mt: 1,
              fontSize: { xs: "0.65rem", sm: "0.75rem" }
            }}
          >
            Accepted formats: {acceptedTypes} (max {maxSizeMB}MB)
          </Typography>
        </label>
      </Paper>
      {error && (
        <Typography color="error" variant="body2" sx={{ mt: 1 }}>
          {error}
        </Typography>
      )}
    </Box>
  );
};

export default FileUploadZone;

