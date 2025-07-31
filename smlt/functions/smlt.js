exports.edgeViewerRequest = (event, context, callback) => {
  const request = event.Records[0].cf.request
  const uri = request.uri

  const redirects = {
    '/5z/P4P': 'https://www.jep-dev.com/vcards/johannes.eimer',
    '/5z/tVx': 'https://www.jep-dev.com/vcards/carola.ludermann',
    '/5z/GFs': 'https://www.jep-dev.com/vcards/elvva.wong',
    '/8k5e/bzb24': 'https://www.tfr-bremen.de',
    '/8k5e/bzf42': 'https://hautarzt-degenhardt.de/',
  }

  if (redirects[uri]) {
    callback(null, {
      status: '301',
      statusDescription: 'Moved Permanently',
      headers: {
        location: [{ key: 'Location', value: redirects[uri] }],
      },
    })
    return
  }

  callback(null, request)
}
