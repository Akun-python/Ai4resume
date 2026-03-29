export const formatTimestamp = (value?: string | null) => {
  if (!value) {
    return '暂无时间记录'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export const shortenJobId = (jobId?: string | null) => {
  if (!jobId) {
    return '未创建'
  }

  if (jobId.length <= 12) {
    return jobId
  }

  return `${jobId.slice(0, 8)}...${jobId.slice(-4)}`
}
