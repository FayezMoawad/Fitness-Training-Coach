export interface Workout {
  id: number;
  coach_id: number;
  name: string;
  description: string | null;
  created_at: string;
}

export type AssignmentStatus = "assigned" | "completed";

export interface Assignment {
  id: number;
  workout_id: number;
  client_id: number;
  assigned_at: string;
  status: AssignmentStatus;
}

export interface ExerciseResult {
  name: string;
  sets: number;
  reps: number;
  weight: number;
}

export interface WorkoutLog {
  id: number;
  assignment_id: number;
  exercises: ExerciseResult[];
  notes: string | null;
  logged_at: string;
}

export interface ClientProgressAssignment {
  assignment_id: number;
  workout_id: number;
  workout_name: string;
  status: AssignmentStatus;
  assigned_at: string;
  logs: WorkoutLog[];
}

export interface ClientProgressResponse {
  client_id: number;
  assignments: ClientProgressAssignment[];
}
