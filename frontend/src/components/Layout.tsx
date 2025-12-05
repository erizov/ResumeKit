import { 
  AppBar, 
  Box, 
  Button, 
  Container, 
  Toolbar, 
  Typography, 
  useMediaQuery, 
  useTheme,
  Avatar,
  Chip,
  Menu,
  MenuItem
} from "@mui/material";
import { Description, Home, History, Logout, Person } from "@mui/icons-material";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";

const Layout: React.FC = () => {
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
    handleMenuClose();
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh", bgcolor: "grey.50" }}>
      <AppBar 
        position="static" 
        elevation={2}
        sx={{ 
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.1)"
        }}
      >
        <Toolbar sx={{ py: { xs: 1, sm: 1.5 } }}>
          <Box sx={{ display: "flex", alignItems: "center", flexGrow: 1, gap: 1.5 }}>
            <Avatar
              sx={{
                bgcolor: "rgba(255, 255, 255, 0.2)",
                width: { xs: 36, sm: 40 },
                height: { xs: 36, sm: 40 },
                border: "2px solid rgba(255, 255, 255, 0.3)"
              }}
            >
              <Description sx={{ fontSize: { xs: 20, sm: 24 } }} />
            </Avatar>
            <Typography 
              variant={isMobile ? "h6" : "h5"} 
              component="div" 
              sx={{ 
                fontWeight: 700,
                letterSpacing: "-0.5px",
                textShadow: "0 2px 4px rgba(0,0,0,0.1)"
              }}
            >
              ResumeKit
            </Typography>
            {!isMobile && (
              <Chip 
                label="AI-Powered" 
                size="small" 
                sx={{ 
                  bgcolor: "rgba(255, 255, 255, 0.2)",
                  color: "white",
                  fontWeight: 500,
                  fontSize: "0.7rem",
                  height: 20
                }} 
              />
            )}
          </Box>
          <Box sx={{ display: "flex", gap: { xs: 0.5, sm: 1 } }}>
            <Button
              color="inherit"
              component={Link}
              to="/"
              startIcon={<Home />}
              size={isMobile ? "small" : "medium"}
              sx={{
                fontWeight: location.pathname === "/" ? 700 : 400,
                minWidth: isMobile ? "auto" : "100px",
                borderRadius: 2,
                px: { xs: 1, sm: 2 },
                bgcolor: location.pathname === "/" ? "rgba(255, 255, 255, 0.15)" : "transparent",
                "&:hover": {
                  bgcolor: "rgba(255, 255, 255, 0.2)",
                },
                transition: "all 0.2s ease-in-out"
              }}
            >
              {isMobile ? "" : "Home"}
            </Button>
            <Button
              color="inherit"
              component={Link}
              to="/history"
              startIcon={<History />}
              size={isMobile ? "small" : "medium"}
              sx={{
                fontWeight: location.pathname === "/history" ? 700 : 400,
                minWidth: isMobile ? "auto" : "100px",
                borderRadius: 2,
                px: { xs: 1, sm: 2 },
                bgcolor: location.pathname === "/history" ? "rgba(255, 255, 255, 0.15)" : "transparent",
                "&:hover": {
                  bgcolor: "rgba(255, 255, 255, 0.2)",
                },
                transition: "all 0.2s ease-in-out"
              }}
            >
              {isMobile ? "" : "History"}
            </Button>
            <Button
              color="inherit"
              onClick={handleMenuOpen}
              startIcon={<Person />}
              size={isMobile ? "small" : "medium"}
              sx={{
                borderRadius: 2,
                px: { xs: 1, sm: 2 },
                "&:hover": {
                  bgcolor: "rgba(255, 255, 255, 0.2)",
                },
                transition: "all 0.2s ease-in-out"
              }}
            >
              {isMobile ? "" : user?.email || "User"}
            </Button>
          </Box>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            anchorOrigin={{
              vertical: "bottom",
              horizontal: "right",
            }}
            transformOrigin={{
              vertical: "top",
              horizontal: "right",
            }}
          >
            {user && (
              <MenuItem disabled>
                <Box>
                  <Typography variant="body2" fontWeight={600}>
                    {user.email}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Level: {user.user_level} resumes
                  </Typography>
                </Box>
              </MenuItem>
            )}
            <MenuItem onClick={handleLogout}>
              <Logout sx={{ mr: 1, fontSize: 20 }} />
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
      <Container 
        maxWidth="lg" 
        sx={{ 
          py: { xs: 3, sm: 4, md: 5 }, 
          px: { xs: 2, sm: 3, md: 4 },
          flexGrow: 1 
        }}
      >
        <Outlet />
      </Container>
      <Box
        component="footer"
        sx={{
          py: 3,
          px: 2,
          mt: "auto",
          bgcolor: "grey.100",
          borderTop: "1px solid",
          borderColor: "grey.300",
          textAlign: "center"
        }}
      >
        <Typography variant="body2" color="text.secondary">
          © {new Date().getFullYear()} ResumeKit - AI-Powered Resume Tailoring
        </Typography>
      </Box>
    </Box>
  );
};

export default Layout;

