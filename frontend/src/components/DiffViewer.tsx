import {
  Box,
  Button,
  ButtonGroup,
  Paper,
  Stack,
  Typography,
  useMediaQuery,
  useTheme
} from "@mui/material";
import { diffLines } from "diff";
import React, { useState } from "react";

interface DiffViewerProps {
  original: string;
  tailored: string;
}

type ViewMode = "original" | "tailored" | "side-by-side" | "unified";

const DiffViewer: React.FC<DiffViewerProps> = ({ original, tailored }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const [viewMode, setViewMode] = useState<ViewMode>("tailored");

  const renderOriginal = () => (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Original Resume
      </Typography>
      <Box
        component="pre"
        sx={{
          whiteSpace: "pre-wrap",
          fontFamily: "monospace",
          fontSize: 12,
          maxHeight: "600px",
          overflow: "auto",
          backgroundColor: "grey.50",
          p: 2,
          borderRadius: 1,
        }}
      >
        {original}
      </Box>
    </Paper>
  );

  const renderTailored = () => (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Tailored Resume
      </Typography>
      <Box
        component="pre"
        sx={{
          whiteSpace: "pre-wrap",
          fontFamily: "monospace",
          fontSize: 12,
          maxHeight: "600px",
          overflow: "auto",
          backgroundColor: "grey.50",
          p: 2,
          borderRadius: 1,
        }}
      >
        {tailored}
      </Box>
    </Paper>
  );

  const renderSideBySide = () => {
    const diff = diffLines(original, tailored);

    return (
      <Paper sx={{ p: { xs: 1, sm: 2 } }}>
        <Typography 
          variant="h6" 
          gutterBottom
          sx={{ fontSize: { xs: "1rem", sm: "1.25rem" } }}
        >
          Side-by-Side Comparison
        </Typography>
        <Stack 
          direction={{ xs: "column", sm: "row" }} 
          spacing={2} 
          sx={{ maxHeight: "600px", overflow: "auto" }}
        >
          <Box sx={{ flex: 1 }}>
            <Typography variant="subtitle2" color="error.main" gutterBottom>
              Original
            </Typography>
            <Box
              component="pre"
              sx={{
                whiteSpace: "pre-wrap",
                fontFamily: "monospace",
                fontSize: 11,
                backgroundColor: "grey.50",
                p: 1,
                borderRadius: 1,
                m: 0,
              }}
            >
              {diff
                .filter((part) => part.removed || !part.added)
                .map((part, i) => (
                  <span
                    key={i}
                    style={{
                      backgroundColor: part.removed ? "#ffcccc" : "transparent",
                    }}
                  >
                    {part.value}
                  </span>
                ))}
            </Box>
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="subtitle2" color="success.main" gutterBottom>
              Tailored
            </Typography>
            <Box
              component="pre"
              sx={{
                whiteSpace: "pre-wrap",
                fontFamily: "monospace",
                fontSize: 11,
                backgroundColor: "grey.50",
                p: 1,
                borderRadius: 1,
                m: 0,
              }}
            >
              {diff
                .filter((part) => part.added || !part.removed)
                .map((part, i) => (
                  <span
                    key={i}
                    style={{
                      backgroundColor: part.added ? "#ccffcc" : "transparent",
                    }}
                  >
                    {part.value}
                  </span>
                ))}
            </Box>
          </Box>
        </Stack>
      </Paper>
    );
  };

  const renderUnified = () => {
    const diff = diffLines(original, tailored);

    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Unified Diff View
        </Typography>
        <Box
          component="pre"
          sx={{
            whiteSpace: "pre-wrap",
            fontFamily: "monospace",
            fontSize: 11,
            maxHeight: "600px",
            overflow: "auto",
            backgroundColor: "grey.50",
            p: 2,
            borderRadius: 1,
          }}
        >
          {diff.map((part, i) => {
            let backgroundColor = "transparent";
            let prefix = " ";
            if (part.added) {
              backgroundColor = "#ccffcc";
              prefix = "+";
            } else if (part.removed) {
              backgroundColor = "#ffcccc";
              prefix = "-";
            }

            return (
              <span
                key={i}
                style={{
                  backgroundColor,
                  display: "block",
                }}
              >
                {part.value
                  .split("\n")
                  .map((line, lineIdx) => (
                    <span key={lineIdx}>
                      {prefix} {line}
                      {lineIdx < part.value.split("\n").length - 1 && "\n"}
                    </span>
                  ))}
              </span>
            );
          })}
        </Box>
      </Paper>
    );
  };

  return (
    <Box>
      <Stack 
        direction={{ xs: "column", sm: "row" }} 
        justifyContent="space-between" 
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        mb={2}
      >
        <Typography 
          variant="h6"
          sx={{ fontSize: { xs: "1.1rem", sm: "1.25rem" } }}
        >
          Resume Comparison
        </Typography>
        <ButtonGroup 
          variant="outlined" 
          size="small"
          orientation={isMobile ? "vertical" : "horizontal"}
          sx={{ width: { xs: "100%", sm: "auto" } }}
        >
          <Button
            variant={viewMode === "original" ? "contained" : "outlined"}
            onClick={() => setViewMode("original")}
            fullWidth={isMobile}
          >
            Original
          </Button>
          <Button
            variant={viewMode === "tailored" ? "contained" : "outlined"}
            onClick={() => setViewMode("tailored")}
            fullWidth={isMobile}
          >
            Tailored
          </Button>
          <Button
            variant={viewMode === "side-by-side" ? "contained" : "outlined"}
            onClick={() => setViewMode("side-by-side")}
            fullWidth={isMobile}
          >
            Side-by-Side
          </Button>
          <Button
            variant={viewMode === "unified" ? "contained" : "outlined"}
            onClick={() => setViewMode("unified")}
            fullWidth={isMobile}
          >
            Unified
          </Button>
        </ButtonGroup>
      </Stack>

      {viewMode === "original" && renderOriginal()}
      {viewMode === "tailored" && renderTailored()}
      {viewMode === "side-by-side" && renderSideBySide()}
      {viewMode === "unified" && renderUnified()}
    </Box>
  );
};

export default DiffViewer;

