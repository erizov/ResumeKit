import { AppBar, Box, Button, Container, Toolbar, Typography, useMediaQuery, useTheme } from "@mui/material";
import { Link, Outlet, useLocation } from "react-router-dom";
import React from "react";

const Layout: React.FC = () => {
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <AppBar position="static">
        <Toolbar>
          <Typography 
            variant={isMobile ? "subtitle1" : "h6"} 
            component="div" 
            sx={{ flexGrow: 1 }}
          >
            ResumeKit
          </Typography>
          <Button
            color="inherit"
            component={Link}
            to="/"
            size={isMobile ? "small" : "medium"}
            sx={{
              fontWeight: location.pathname === "/" ? "bold" : "normal",
              minWidth: isMobile ? "auto" : "64px",
            }}
          >
            Home
          </Button>
          <Button
            color="inherit"
            component={Link}
            to="/history"
            size={isMobile ? "small" : "medium"}
            sx={{
              fontWeight: location.pathname === "/history" ? "bold" : "normal",
              minWidth: isMobile ? "auto" : "64px",
            }}
          >
            History
          </Button>
        </Toolbar>
      </AppBar>
      <Container 
        maxWidth="lg" 
        sx={{ 
          py: { xs: 2, sm: 3, md: 4 }, 
          px: { xs: 1, sm: 2, md: 3 },
          flexGrow: 1 
        }}
      >
        <Outlet />
      </Container>
    </Box>
  );
};

export default Layout;

