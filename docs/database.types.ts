export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  graphql_public: {
    Tables: {
      [_ in never]: never
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      graphql: {
        Args: {
          operationName?: string
          query?: string
          variables?: Json
          extensions?: Json
        }
        Returns: Json
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
  public: {
    Tables: {
      ai_generation_events: {
        Row: {
          accepted_cards_count: number
          cost: number | null
          created_at: string
          generated_cards_count: number
          id: string
          llm_model_used: string | null
          rejected_cards_count: number
          source_text_id: string
          updated_at: string
          user_id: string
        }
        Insert: {
          accepted_cards_count?: number
          cost?: number | null
          created_at?: string
          generated_cards_count?: number
          id?: string
          llm_model_used?: string | null
          rejected_cards_count?: number
          source_text_id: string
          updated_at?: string
          user_id: string
        }
        Update: {
          accepted_cards_count?: number
          cost?: number | null
          created_at?: string
          generated_cards_count?: number
          id?: string
          llm_model_used?: string | null
          rejected_cards_count?: number
          source_text_id?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "ai_generation_events_source_text_id_fkey"
            columns: ["source_text_id"]
            isOneToOne: false
            referencedRelation: "source_texts"
            referencedColumns: ["id"]
          },
        ]
      }
      flashcards: {
        Row: {
          back_content: string
          created_at: string
          front_content: string
          id: string
          source: Database["public"]["Enums"]["flashcard_source_enum"]
          source_text_id: string | null
          status: Database["public"]["Enums"]["flashcard_status_enum"]
          updated_at: string
          user_id: string
        }
        Insert: {
          back_content: string
          created_at?: string
          front_content: string
          id?: string
          source: Database["public"]["Enums"]["flashcard_source_enum"]
          source_text_id?: string | null
          status: Database["public"]["Enums"]["flashcard_status_enum"]
          updated_at?: string
          user_id: string
        }
        Update: {
          back_content?: string
          created_at?: string
          front_content?: string
          id?: string
          source?: Database["public"]["Enums"]["flashcard_source_enum"]
          source_text_id?: string | null
          status?: Database["public"]["Enums"]["flashcard_status_enum"]
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "flashcards_source_text_id_fkey"
            columns: ["source_text_id"]
            isOneToOne: false
            referencedRelation: "source_texts"
            referencedColumns: ["id"]
          },
        ]
      }
      source_texts: {
        Row: {
          created_at: string
          id: string
          text_content: string
          updated_at: string
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: string
          text_content: string
          updated_at?: string
          user_id: string
        }
        Update: {
          created_at?: string
          id?: string
          text_content?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      user_flashcard_spaced_repetition: {
        Row: {
          created_at: string
          current_interval: number
          data_extra: Json | null
          due_date: string
          flashcard_id: string
          id: string
          last_reviewed_at: string | null
          updated_at: string
          user_id: string
        }
        Insert: {
          created_at?: string
          current_interval?: number
          data_extra?: Json | null
          due_date?: string
          flashcard_id: string
          id?: string
          last_reviewed_at?: string | null
          updated_at?: string
          user_id: string
        }
        Update: {
          created_at?: string
          current_interval?: number
          data_extra?: Json | null
          due_date?: string
          flashcard_id?: string
          id?: string
          last_reviewed_at?: string | null
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "user_flashcard_spaced_repetition_flashcard_id_fkey"
            columns: ["flashcard_id"]
            isOneToOne: false
            referencedRelation: "flashcards"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      flashcard_source_enum: "manual" | "ai_suggestion"
      flashcard_status_enum: "active" | "pending_review" | "rejected"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DefaultSchema = Database[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof Database },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof (Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        Database[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof Database }
  ? (Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      Database[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof Database },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof Database }
  ? Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof Database },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof Database }
  ? Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof Database },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof Database[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends { schema: keyof Database }
  ? Database[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof Database },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends { schema: keyof Database }
  ? Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  graphql_public: {
    Enums: {},
  },
  public: {
    Enums: {
      flashcard_source_enum: ["manual", "ai_suggestion"],
      flashcard_status_enum: ["active", "pending_review", "rejected"],
    },
  },
} as const

