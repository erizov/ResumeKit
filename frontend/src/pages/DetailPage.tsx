import {
  Box,
  Button,
  Chip,
  LinearProgress,
  Paper,
  Stack,
  Typography,
  Snackbar,
  Alert,
  useMediaQuery,
  useTheme
} from "@mui/material";
import { ContentCopy } from "@mui/icons-material";
import { useNavigate, useParams } from "react-router-dom";
import React, { useEffect, useState } from "react";
import DiffViewer from "../components/DiffViewer";

type TailoredResumeDetail = {
  id: number;
  created_at: string;
  language: string;
  target: string;
  content: string;
  notes: string | null;
  base_resume_text: string;
  job_description: string;
};

type KeywordCoverage = {
  matched: string[];
  missing: string[];
  score: number;
  total_jd_keywords: number;
  total_resume_keywords: number;
};

const DetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const [detail, setDetail] = useState<TailoredResumeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);
  const [coverage, setCoverage] = useState<KeywordCoverage | null>(null);
  const [loadingCoverage, setLoadingCoverage] = useState(false);

  useEffect(() => {
    const fetchDetail = async () => {
      if (!id) {
        setError("Invalid resume ID");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`/api/tailor/${id}`);
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error("Resume not found");
          }
          throw new Error(`HTTP error ${response.status}`);
        }
        const data: TailoredResumeDetail = await response.json();
        setDetail(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load resume");
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [id]);

  useEffect(() => {
    const fetchCoverage = async () => {
      if (!id) return;

      setLoadingCoverage(true);
      try {
        const response = await fetch(`/api/tailor/${id}/coverage`);
        if (response.ok) {
          const data: KeywordCoverage = await response.json();
          setCoverage(data);
        }
      } catch (err) {
        // Coverage is optional, don't show error
        console.error("Failed to load coverage:", err);
      } finally {
        setLoadingCoverage(false);
      }
    };

    if (detail) {
      fetchCoverage();
    }
  }, [id, detail]);

  const handleDownloadPDF = () => {
    if (!id) return;
    window.open(`/api/tailor/${id}/pdf`, "_blank");
  };

  const handleCopyToClipboard = async () => {
    if (!detail) return;
    try {
      await navigator.clipboard.writeText(detail.content);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 3000);
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement("textarea");
      textArea.value = detail.content;
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand("copy");
        setCopySuccess(true);
        setTimeout(() => setCopySuccess(false), 3000);
      } catch (fallbackErr) {
        console.error("Failed to copy:", fallbackErr);
      }
      document.body.removeChild(textArea);
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading) {
    return <LinearProgress />;
  }

  if (error) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography color="error" variant="h6" gutterBottom>
          Error
        </Typography>
        <Typography color="error" variant="body1">
          {error}
        </Typography>
        <Button sx={{ mt: 2 }} onClick={() => navigate("/history")}>
          Back to History
        </Button>
      </Paper>
    );
  }

  if (!detail) {
    return null;
  }

  return (
    <>
      <Stack 
        direction={{ xs: "column", sm: "row" }} 
        justifyContent="space-between" 
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        mb={2}
      >
        <Typography 
          variant="h4"
          sx={{ fontSize: { xs: "1.5rem", sm: "2.125rem" } }}
        >
          Tailored Resume #{detail.id}
        </Typography>
        <Button 
          onClick={() => navigate("/history")}
          size={isMobile ? "small" : "medium"}
          fullWidth={isMobile}
        >
          Back to History
        </Button>
      </Stack>

      <Paper sx={{ p: { xs: 2, sm: 3 }, mb: 2 }}>
        <Stack spacing={2}>
          <Stack 
            direction={{ xs: "column", sm: "row" }} 
            spacing={{ xs: 1, sm: 2 }} 
            alignItems={{ xs: "flex-start", sm: "center" }}
            flexWrap="wrap"
          >
            <Typography 
              variant="body2" 
              color="text.secondary"
              sx={{ fontSize: { xs: "0.75rem", sm: "0.875rem" } }}
            >
              Created: {formatDate(detail.created_at)}
            </Typography>
            <Chip 
              label={detail.language.toUpperCase()} 
              size="small"
              sx={{ fontSize: { xs: "0.7rem", sm: "0.75rem" } }}
            />
            <Chip
              label={detail.target.replace("_", " ")}
              size="small"
              color="primary"
              sx={{ fontSize: { xs: "0.7rem", sm: "0.75rem" } }}
            />
          </Stack>

          {detail.notes && (
            <Box>
              <Typography 
                variant="subtitle2" 
                gutterBottom
                sx={{ fontSize: { xs: "0.875rem", sm: "1rem" } }}
              >
                Notes:
              </Typography>
              <Typography 
                variant="body2" 
                color="text.secondary"
                sx={{ fontSize: { xs: "0.75rem", sm: "0.875rem" } }}
              >
                {detail.notes}
              </Typography>
            </Box>
          )}

          <Stack 
            direction={{ xs: "column", sm: "row" }} 
            spacing={2}
            sx={{ "& > *": { width: { xs: "100%", sm: "auto" } } }}
          >
            <Button
              variant="contained"
              startIcon={<ContentCopy />}
              onClick={handleCopyToClipboard}
              fullWidth={isMobile}
            >
              Copy to Clipboard
            </Button>
            <Button
              variant="contained"
              onClick={handleDownloadPDF}
              fullWidth={isMobile}
            >
              Download PDF
            </Button>
          </Stack>
        </Stack>
      </Paper>

      {coverage && (
        <Paper sx={{ p: 3, mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Keyword Coverage Analysis
          </Typography>
          <Stack spacing={2}>
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Coverage Score: {(coverage.score * 100).toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {coverage.matched.length} of {coverage.total_jd_keywords} keywords matched
              </Typography>
            </Box>

            {coverage.matched.length > 0 && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Matched Keywords:
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {coverage.matched.map((keyword) => (
                    <Chip
                      key={keyword}
                      label={keyword}
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                  ))}
                </Stack>
              </Box>
            )}

            {coverage.missing.length > 0 && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Missing Keywords:
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {coverage.missing.map((keyword) => (
                    <Chip
                      key={keyword}
                      label={keyword}
                      size="small"
                      color="error"
                      variant="outlined"
                    />
                  ))}
                </Stack>
              </Box>
            )}
          </Stack>
        </Paper>
      )}

      <Box sx={{ mb: 2 }}>
        <DiffViewer original={detail.base_resume_text} tailored={detail.content} />
      </Box>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Job Description
        </Typography>
        <Box
          component="pre"
          sx={{
            whiteSpace: "pre-wrap",
            fontFamily: "monospace",
            fontSize: 12,
            maxHeight: "300px",
            overflow: "auto",
            color: "text.secondary"
          }}
        >
          {detail.job_description}
        </Box>
      </Paper>

      <Snackbar
        open={copySuccess}
        autoHideDuration={3000}
        onClose={() => setCopySuccess(false)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity="success" onClose={() => setCopySuccess(false)}>
          Resume content copied to clipboard!
        </Alert>
      </Snackbar>
    </>
  );
};

export default DetailPage;

