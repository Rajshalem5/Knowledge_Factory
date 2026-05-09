import { api } from './client';

export interface TestCase {
  input: string;
  expected_output: string;
  is_public: boolean;
}

export interface QuestionPublicView {
  id: string;
  title: string;
  description: string;
  difficulty: 'easy' | 'medium' | 'hard';
  boilerplate: Record<string, string>;
  public_test_cases: TestCase[];
}

export interface GenerateRequest {
  topic?: string;
  difficulty?: string;
  num_public_cases?: number;
  num_private_cases?: number;
}

export const questionsApi = {
  generate: (req: GenerateRequest) =>
    api.post<QuestionPublicView>('/api/questions/generate', req),

  getPublic: (id: string) =>
    api.get<QuestionPublicView>(`/api/questions/${id}/public`),
};
