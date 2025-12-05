from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

from services import MonitoringService, SummarizationService

load_dotenv()

executor = ThreadPoolExecutor()
executor.submit(SummarizationService.start)
executor.submit(MonitoringService.start)

# wait til jobs are done, which will never happen since they're infinite loops :)
executor.shutdown(wait=True)
