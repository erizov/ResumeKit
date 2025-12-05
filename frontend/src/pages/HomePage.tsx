import {
  Box,
  Button,
  LinearProgress,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
  IconButton,
  Snackbar,
  Alert,
  Chip
} from "@mui/material";
import { ContentCopy, Close } from "@mui/icons-material";
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import FileUploadZone from "../components/FileUploadZone";
import { fetchWithRetry, getErrorMessage, isOnline } from "../utils/apiClient";

type TailoredResume = {
  id: number;
  language: string;
  target: string;
  content: string;
  notes?: string | null;
};

type RecommendResult = {
  resumes: TailoredResume[];
};

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [jobDescription, setJobDescription] = useState("");
  const [jobUrl, setJobUrl] = useState("");
  const [fetchingJob, setFetchingJob] = useState(false);
  const [resumeText, setResumeText] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [languages, setLanguages] = useState("en,ru");
  const [targets, setTargets] = useState("backend,gpt_engineer");
  const [aggressiveness, setAggressiveness] = useState(2);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RecommendResult | null>(null);
  const [copySuccess, setCopySuccess] = useState<string | null>(null);
  const [offline, setOffline] = useState(!isOnline());

  useEffect(() => {
    const handleOnline = () => setOffline(false);
    const handleOffline = () => setOffline(true);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setResult(null);

    // Job description or URL is required
    if (!jobDescription && !jobUrl.trim()) {
      setError("Please provide either a job description or a job URL.");
      return;
    }

    if (!resumeText && !resumeFile) {
      setError("Provide either resume text or upload a resume file.");
      return;
    }

    const formData = new FormData();
    // Always send these fields (even if empty) to satisfy FastAPI form validation
    formData.append("job_description", jobDescription || "");
    formData.append("job_url", jobUrl.trim() || "");
    if (resumeFile) {
      formData.append("resume_file", resumeFile);
    } else {
      formData.append("resume_text", resumeText);
    }
    formData.append("languages", languages);
    formData.append("targets", targets);
    formData.append("aggressiveness", String(aggressiveness));

    if (offline) {
      setError("You are currently offline. Please check your internet connection.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetchWithRetry("/api/recommend", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorMessage = await getErrorMessage(response);
        throw new Error(errorMessage);
      }

      const data: RecommendResult = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ): void => {
    const file = event.target.files?.[0] ?? null;
    setResumeFile(file);
  };

  const handleFetchJobUrl = async () => {
    if (!jobUrl.trim()) {
      setError("Please enter a job URL");
      return;
    }

    setFetchingJob(true);
    setError(null);
    try {
      const response = await fetchWithRetry("/api/job/fetch", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ url: jobUrl })
      });

      if (!response.ok) {
        const errorMessage = await getErrorMessage(response);
        throw new Error(errorMessage);
      }

      const data = await response.json();
      // API returns 'text' field based on JobFetchResponse schema
      setJobDescription(data.text || data.job_description || "");
      setJobUrl(""); // Clear URL after successful fetch
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch job description");
    } finally {
      setFetchingJob(false);
    }
  };

  const handleViewDetail = (id: number) => {
    navigate(`/tailor/${id}`);
  };

  const handleCopyToClipboard = async (content: string, id: number) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopySuccess(`Resume #${id} copied!`);
      setTimeout(() => setCopySuccess(null), 3000);
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement("textarea");
      textArea.value = content;
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand("copy");
        setCopySuccess(`Resume #${id} copied!`);
        setTimeout(() => setCopySuccess(null), 3000);
      } catch (fallbackErr) {
        console.error("Failed to copy:", fallbackErr);
      }
      document.body.removeChild(textArea);
    }
  };

  return (
    <>
      <Box sx={{ mb: 4 }}>
        <Typography 
          variant="h4" 
          gutterBottom
          sx={{ 
            fontSize: { xs: "1.75rem", sm: "2.125rem", md: "2.5rem" },
            fontWeight: 700,
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            mb: 1
          }}
        >
          Tailor Your Resume to Any Job
        </Typography>
        <Typography 
          variant="body1" 
          color="text.secondary"
          sx={{ fontSize: { xs: "0.95rem", sm: "1.1rem" } }}
        >
          Upload your resume and job description to get AI-powered, tailored resumes optimized for each position
        </Typography>
      </Box>

      <Paper 
        sx={{ 
          p: { xs: 3, sm: 4, md: 5 }, 
          mb: { xs: 3, sm: 4 },
          background: "linear-gradient(to bottom, #ffffff 0%, #f8f9ff 100%)",
          border: "1px solid rgba(102, 126, 234, 0.1)"
        }} 
        elevation={2}
      >
        <form onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField
                label="Job posting URL (optional)"
                placeholder="https://example.com/job-posting"
                value={jobUrl}
                onChange={(e) => setJobUrl(e.target.value)}
                fullWidth
                disabled={fetchingJob}
              />
              <Button
                variant="outlined"
                onClick={(e) => {
                  e.preventDefault();
                  handleFetchJobUrl();
                }}
                disabled={fetchingJob || !jobUrl.trim()}
                sx={{ minWidth: 150 }}
              >
                {fetchingJob ? "Fetching..." : "Fetch from URL"}
              </Button>
            </Stack>

            <TextField
              label="Job description or job ad text"
              multiline
              minRows={4}
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              fullWidth
              helperText="Paste job description text or fetch from URL above"
            />

            <TextField
              label="Resume text (optional if uploading file)"
              multiline
              minRows={4}
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              fullWidth
              disabled={!!resumeFile}
              helperText={resumeFile ? "File uploaded - text input disabled" : "Paste resume text or upload file below"}
            />

            <FileUploadZone
              onFileSelect={(file) => {
                setResumeFile(file);
                setResumeText(""); // Clear text when file is selected
              }}
              acceptedTypes=".docx,.doc,.pdf"
              maxSizeMB={10}
            />

            {resumeFile && (
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Chip
                  label={`${resumeFile.name} (${(resumeFile.size / 1024).toFixed(1)} KB)`}
                  color="primary"
                  onDelete={() => {
                    setResumeFile(null);
                  }}
                  deleteIcon={<Close />}
                />
              </Box>
            )}

            <Stack 
              direction={{ xs: "column", sm: "row" }} 
              spacing={2}
              sx={{ "& > *": { minWidth: { xs: "100%", sm: "auto" } } }}
            >
              <TextField
                label="Languages"
                helperText="Comma separated, e.g. en,ru"
                value={languages}
                onChange={(e) => setLanguages(e.target.value)}
                fullWidth
                size="small"
              />
              <TextField
                label="Targets"
                helperText="Comma separated, e.g. backend,gpt_engineer"
                value={targets}
                onChange={(e) => setTargets(e.target.value)}
                fullWidth
                size="small"
              />
              <TextField
                select
                label="Aggressiveness"
                value={aggressiveness}
                onChange={(e) => setAggressiveness(Number(e.target.value))}
                fullWidth
                size="small"
              >
                <MenuItem value={1}>1 – minimal</MenuItem>
                <MenuItem value={2}>2 – balanced</MenuItem>
                <MenuItem value={3}>3 – aggressive</MenuItem>
              </TextField>
            </Stack>

            {loading && <LinearProgress />}
            {offline && (
              <Paper sx={{ p: 2, bgcolor: "warning.light", mb: 2 }}>
                <Typography color="warning.dark" variant="body2">
                  You are currently offline. Please check your internet connection.
                </Typography>
              </Paper>
            )}
            {error && (
              <Typography color="error" variant="body2">
                {error}
              </Typography>
            )}

            <Box sx={{ pt: 1 }}>
              <Button
                variant="contained"
                type="submit"
                disabled={loading}
                fullWidth={false}
                size="large"
                sx={{ 
                  minWidth: { xs: "100%", sm: "250px" },
                  py: 1.5,
                  px: 4,
                  fontSize: "1rem",
                  fontWeight: 600,
                  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  boxShadow: "0 4px 12px rgba(102, 126, 234, 0.4)",
                  "&:hover": {
                    background: "linear-gradient(135deg, #764ba2 0%, #667eea 100%)",
                    boxShadow: "0 6px 16px rgba(102, 126, 234, 0.5)",
                    transform: "translateY(-2px)"
                  },
                  transition: "all 0.3s ease-in-out"
                }}
              >
                {loading ? "Generating..." : "Generate Tailored Resumes"}
              </Button>
            </Box>
          </Stack>
        </form>
      </Paper>

      {result && (
        <Stack spacing={3} sx={{ mt: 4 }}>
          <Typography 
            variant="h5"
            sx={{ 
              fontSize: { xs: "1.5rem", sm: "1.75rem", md: "2rem" },
              fontWeight: 700,
              color: "primary.main"
            }}
          >
            Generated Resumes
          </Typography>
          {result.resumes.map((resume) => (
            <Paper 
              key={`${resume.id || resume.language}-${resume.target}`} 
              sx={{ 
                p: { xs: 2, sm: 3 },
                border: "1px solid rgba(102, 126, 234, 0.1)",
                transition: "all 0.3s ease-in-out",
                "&:hover": {
                  boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
                  transform: "translateY(-2px)"
                }
              }}
              elevation={1}
            >
              <Stack 
                direction={{ xs: "column", sm: "row" }} 
                justifyContent="space-between" 
                alignItems={{ xs: "flex-start", sm: "center" }}
                spacing={1}
                mb={1}
              >
                <Typography 
                  variant="subtitle1"
                  sx={{ fontSize: { xs: "0.95rem", sm: "1rem" } }}
                >
                  {resume.language.toUpperCase()} – {resume.target}
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {resume.id && (
                    <>
                      <IconButton
                        size="small"
                        onClick={() => handleCopyToClipboard(resume.content, resume.id!)}
                        title="Copy to clipboard"
                        sx={{ fontSize: { xs: "0.875rem", sm: "1rem" } }}
                      >
                        <ContentCopy fontSize="small" />
                      </IconButton>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => handleViewDetail(resume.id!)}
                        sx={{ fontSize: { xs: "0.75rem", sm: "0.875rem" } }}
                      >
                        View Details
                      </Button>
                    </>
                  )}
                </Stack>
              </Stack>
              {resume.notes && (
                <Typography 
                  variant="caption" 
                  color="text.secondary" 
                  display="block"
                  sx={{ fontSize: { xs: "0.7rem", sm: "0.75rem" } }}
                >
                  {resume.notes}
                </Typography>
              )}
              <Box
                component="pre"
                sx={{
                  mt: 1,
                  whiteSpace: "pre-wrap",
                  fontFamily: "monospace",
                  fontSize: { xs: 11, sm: 14 },
                  overflowX: "auto",
                  maxWidth: "100%",
                }}
              >
                {resume.content}
              </Box>
            </Paper>
          ))}
        </Stack>
      )}

      <Snackbar
        open={copySuccess !== null}
        autoHideDuration={3000}
        onClose={() => setCopySuccess(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity="success" onClose={() => setCopySuccess(null)}>
          {copySuccess}
        </Alert>
      </Snackbar>
    </>
  );
};

export default HomePage;

