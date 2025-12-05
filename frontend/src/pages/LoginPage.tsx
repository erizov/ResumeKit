import {
  Box,
  Button,
  Container,
  Paper,
  TextField,
  Typography,
  Alert,
  Avatar,
  Stack
} from "@mui/material";
import { Description, Lock } from "@mui/icons-material";
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState("admin");
  const [password, setPassword] = useState("admin");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Login failed");
      }

      const data = await response.json();
      
      // Fetch user info to get user_level
      const userResponse = await fetch("/api/auth/me", {
        headers: {
          Authorization: `Bearer ${data.access_token}`,
        },
      });
      
      if (userResponse.ok) {
        const userData = await userResponse.json();
        login(data.access_token, userData);
        navigate("/");
      } else {
        throw new Error("Failed to fetch user information");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={8}
          sx={{
            p: { xs: 3, sm: 5 },
            borderRadius: 3,
            background: "linear-gradient(to bottom, #ffffff 0%, #f8f9ff 100%)",
          }}
        >
          <Stack spacing={3} alignItems="center">
            {/* Logo/Image Section */}
            <Box
              sx={{
                width: 120,
                height: 120,
                borderRadius: "50%",
                background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                mb: 2,
                boxShadow: "0 8px 24px rgba(102, 126, 234, 0.3)",
              }}
            >
              <Description sx={{ fontSize: 64, color: "white" }} />
            </Box>

            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
                textAlign: "center",
              }}
            >
              Welcome to ResumeKit
            </Typography>

            <Typography
              variant="body1"
              color="text.secondary"
              sx={{ textAlign: "center", mb: 2 }}
            >
              Sign in to access AI-powered resume tailoring
            </Typography>

            {error && (
              <Alert severity="error" sx={{ width: "100%" }}>
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit} sx={{ width: "100%" }}>
              <Stack spacing={3}>
                <TextField
                  label="Email or Username"
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  fullWidth
                  autoFocus
                  InputProps={{
                    startAdornment: (
                      <Avatar sx={{ width: 24, height: 24, mr: 1, bgcolor: "primary.main" }}>
                        <Lock sx={{ fontSize: 16 }} />
                      </Avatar>
                    ),
                  }}
                />

                <TextField
                  label="Password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  fullWidth
                  InputProps={{
                    startAdornment: (
                      <Lock sx={{ fontSize: 20, mr: 1, color: "text.secondary" }} />
                    ),
                  }}
                />

                <Button
                  type="submit"
                  variant="contained"
                  fullWidth
                  size="large"
                  disabled={loading}
                  sx={{
                    py: 1.5,
                    fontSize: "1rem",
                    fontWeight: 600,
                    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    boxShadow: "0 4px 12px rgba(102, 126, 234, 0.4)",
                    "&:hover": {
                      background: "linear-gradient(135deg, #764ba2 0%, #667eea 100%)",
                      boxShadow: "0 6px 16px rgba(102, 126, 234, 0.5)",
                      transform: "translateY(-2px)",
                    },
                    transition: "all 0.3s ease-in-out",
                  }}
                >
                  {loading ? "Signing in..." : "Sign In"}
                </Button>
              </Stack>
            </Box>

            <Typography variant="caption" color="text.secondary" sx={{ mt: 2 }}>
              Default credentials: admin / admin
            </Typography>
          </Stack>
        </Paper>
      </Container>
    </Box>
  );
};

export default LoginPage;

