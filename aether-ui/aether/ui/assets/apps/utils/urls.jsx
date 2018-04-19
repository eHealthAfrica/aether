const baseUrl = process.env.HOSTNAME

export default {
  MOCK_PIPELINES_URL: '/api/ui/pipelines.json',
  PIPELINE_URL: `${baseUrl}/pipeline`
}
