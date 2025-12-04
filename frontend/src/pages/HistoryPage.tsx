import {
  Box,
  Button,
  Chip,
  LinearProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import React, { useEffect, useState } from "react";

type TailoredResumeSummary = {
  id: number;
  created_at: string;
  language: string;
  target: string;
};

type HistoryResponse = {
  items: TailoredResumeSummary[];
  total: number;
};

const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch("/api/history?limit=50");
        if (!response.ok) {
          throw new Error(`HTTP error ${response.status}`);
        }
        const data: HistoryResponse = await response.json();
        setHistory(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load history");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading) {
    return <LinearProgress />;
  }

  if (error) {
    return (
      <Typography color="error" variant="body1">
        {error}
      </Typography>
    );
  }

  return (
    <>
      <Typography 
        variant="h4" 
        gutterBottom
        sx={{ fontSize: { xs: "1.75rem", sm: "2.125rem" } }}
      >
        Resume History
      </Typography>

      {history && history.items.length === 0 ? (
        <Paper sx={{ p: { xs: 2, sm: 3 } }}>
          <Typography variant="body1" color="text.secondary">
            No tailored resumes yet. Generate some from the Home page!
          </Typography>
        </Paper>
      ) : (
        <TableContainer 
          component={Paper}
          sx={{ 
            maxWidth: "100%",
            overflowX: "auto",
          }}
        >
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                  ID
                </TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Language</TableCell>
                <TableCell>Target Role</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {history?.items.map((item) => (
                <TableRow key={item.id} hover>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {item.id}
                  </TableCell>
                  <TableCell sx={{ fontSize: { xs: "0.75rem", sm: "0.875rem" } }}>
                    {formatDate(item.created_at)}
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={item.language.toUpperCase()} 
                      size="small"
                      sx={{ fontSize: { xs: "0.7rem", sm: "0.75rem" } }}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={item.target.replace("_", " ")}
                      size="small"
                      color="primary"
                      sx={{ fontSize: { xs: "0.7rem", sm: "0.75rem" } }}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => navigate(`/tailor/${item.id}`)}
                      sx={{ fontSize: { xs: "0.7rem", sm: "0.875rem" } }}
                    >
                      View
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {history && history.total > history.items.length && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Showing {history.items.length} of {history.total} resumes
          </Typography>
        </Box>
      )}
    </>
  );
};

export default HistoryPage;

