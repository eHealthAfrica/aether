const baseUrl = process.env.HOSTNAME

export default {
  MOCK_PIPELINES_URL: 'http://ui:8004/static/mock/pipelines.mock.json',
  PIPELINE_URL: `${baseUrl}/pipeline`
}
