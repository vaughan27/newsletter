export type Role = "admin" | "manager";

export interface User {
  id: number;
  username: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: User;
}

export interface Newsletter {
  id: number;
  title: string;
  description: string;
  publication_date: string; // YYYY-MM-DD
  cover_url: string;
  pdf_url: string;
  download_url: string;
  cover_source: "slide" | "custom";
  page_count: number;
  pdf_size_bytes: number;
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  timezone: string;
  range_days: number;
  totals: { newsletters: number; visits: number; unique_visitors: number; downloads: number };
  today: { visits: number; unique_visitors: number; downloads: number };
  downloads_by_newsletter: {
    id: number;
    title: string;
    publication_date: string;
    views: number;
    downloads: number;
  }[];
  recent_downloads: { newsletter_id: number; title: string; downloaded_at: string }[];
  daily_traffic: { date: string; visits: number; unique_visitors: number; downloads: number }[];
}
