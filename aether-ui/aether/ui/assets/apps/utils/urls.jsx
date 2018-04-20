const baseUrl = process.env.HOSTNAME

export default {
  MOCK_PIPELINES_URL: '/static/mock/pipelines.mock.json',
  PIPELINE_URL: `${baseUrl}/pipeline`
}
